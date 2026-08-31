from __future__ import annotations

import hashlib
import json
import secrets
import shutil
import tempfile
from pathlib import Path
from threading import RLock
from typing import Any

from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.borrador_importacion_biblioteca import CanonicalRecipeMatcher, normalize_text
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.motor_escritura_segura_i1342 import MotorEscrituraSeguraI1342
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


RECIPE_PATH = "DATOS/db/biblioteca_recetas_601.json"
LEGACY_SOURCE_TYPE = "ESCANDALLO_555A"
LEGACY_WITHOUT_CANONICAL = "EXISTE_EN_LEGACY_SIN_CANONICALIZAR"


class LegacyCanonicalizationError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class LegacyRecipeCanonicalizationService:
    """Puente controlado 555A -> RecetaBiblioteca601; nunca toca Stock."""

    _lock = RLock()

    def __init__(self, base_dir: Path | str) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.legacy = RepositorioEscandallos(
            self.base_dir / "DATOS" / "db" / "escandallos_canonicos.json"
        )
        self.recipes = RepositorioBibliotecaRecetas601(self.base_dir)
        self.products = RepositorioProductosMaestro601(self.base_dir)
        self._pending: dict[str, dict[str, Any]] = {}
        self._completed: dict[str, dict[str, Any]] = {}

    def analyze(self) -> dict[str, Any]:
        cases = [self._case(item) for item in self.legacy.listar()]
        counts: dict[str, int] = {}
        for item in cases:
            counts[item["estado"]] = counts.get(item["estado"], 0) + 1
        return {
            "ok": True, "casos": cases, "contadores": counts,
            "solo_previsualizacion": True, "datos_reales_modificados": False,
        }

    def preview(
        self, *, legacy_ids: list[str] | None, context: AuthorizedExecutionContext
    ) -> dict[str, Any]:
        self._authorize(context, write=False)
        requested = {normalize_text(item) for item in (legacy_ids or []) if normalize_text(item)}
        analysis = self.analyze()
        selected = [item for item in analysis["casos"] if (
            item["estado"] == LEGACY_WITHOUT_CANONICAL
            and (not requested or normalize_text(item["legacy_source_id"]) in requested)
        )]
        if requested - {normalize_text(item["legacy_source_id"]) for item in selected}:
            raise LegacyCanonicalizationError(
                "legacy_not_canonicalizable",
                "Alguna elaboración solicitada ya está enlazada o requiere revisión.",
            )
        token = secrets.token_urlsafe(32)
        self._pending[token] = {
            "actor": self._actor(context), "cases": selected,
            "fingerprint": self._fingerprint(),
        }
        return {
            "ok": True, "estado": "LISTO_PARA_CONFIRMAR",
            "preview_token": token, "requiere_confirmacion": bool(selected),
            "canonicalizaciones": selected,
            "resumen_impacto": {
                "recetas_601": len(selected), "stock": 0, "lotes": 0,
                "movimientos_stock": 0, "recepciones": 0, "compras": 0,
            },
            "datos_reales_modificados": False,
        }

    def confirm(
        self, *, preview_token: str, context: AuthorizedExecutionContext
    ) -> dict[str, Any]:
        token = str(preview_token or "").strip()
        with self._lock:
            completed = self._completed.get(token)
            if completed:
                if completed["actor"] != self._actor(context):
                    raise LegacyCanonicalizationError("invalid_preview", "La vista previa pertenece a otro actor.")
                return {**completed["result"], "idempotente": True}
            pending = self._pending.get(token)
            if not pending or pending["actor"] != self._actor(context):
                raise LegacyCanonicalizationError("invalid_preview", "Vista previa inválida.")
            self._authorize(context, write=True)
            if pending["fingerprint"] != self._fingerprint():
                raise LegacyCanonicalizationError("stale_preview", "Biblioteca o legacy cambiaron desde el preview.")
            result = self._apply(list(pending["cases"]), token)
            self._pending.pop(token, None)
            self._completed[token] = {"actor": pending["actor"], "result": result}
            return result

    def _apply(self, cases: list[dict[str, Any]], token: str) -> dict[str, Any]:
        if not cases:
            return {
                "ok": True, "estado": "SIN_CAMBIOS", "recetas": [],
                "idempotente": True, "datos_reales_modificados": False,
            }
        with tempfile.TemporaryDirectory(prefix="hostai-legacy-canonical-") as raw_dir:
            sandbox = Path(raw_dir)
            target = sandbox / RECIPE_PATH
            target.parent.mkdir(parents=True, exist_ok=True)
            source = self.base_dir / RECIPE_PATH
            if source.exists():
                shutil.copy2(source, target)
            sandbox_repo = RepositorioBibliotecaRecetas601(sandbox)
            created: list[dict[str, Any]] = []
            legacy_to_canonical: dict[str, str] = {}
            ordered = self._dependency_order(cases)
            for case in ordered:
                existing = self._linked_recipe(case["legacy_source_id"], sandbox_repo)
                if existing:
                    legacy_to_canonical[normalize_text(case["legacy_source_id"])] = existing["id"]
                    legacy_to_canonical[normalize_text(case["nombre"])] = existing["id"]
                    created.append(existing)
                    continue
                payload = self._recipe_payload(case, legacy_to_canonical)
                result = sandbox_repo.crear_incompleta_desde_importacion(payload)
                if not result.get("ok"):
                    raise LegacyCanonicalizationError(
                        "canonicalization_failed", "; ".join(result.get("errores") or [])
                    )
                recipe = result["receta"]
                legacy_to_canonical[normalize_text(case["legacy_source_id"])] = recipe["id"]
                legacy_to_canonical[normalize_text(case["nombre"])] = recipe["id"]
                created.append(recipe)
            # Segunda pasada: resuelve dependencias aunque el orden legacy sea imperfecto.
            for case in ordered:
                recipe_id = legacy_to_canonical[normalize_text(case["legacy_source_id"])]
                current = sandbox_repo.obtener(recipe_id)
                structured = []
                dependencies: list[str] = []
                for ingredient in case["ingredientes"]:
                    dependency = legacy_to_canonical.get(normalize_text(ingredient.get("legacy_dependency_id")))
                    if dependency:
                        dependencies.append(dependency)
                    structured.append({
                        "nombre_original": ingredient["nombre"],
                        "article_id": ingredient.get("article_id"),
                        "elaboracion_id": dependency,
                        "cantidad": ingredient.get("cantidad"), "unidad": ingredient.get("unidad"),
                    })
                history = list((current or {}).get("historial_procedencia") or [])
                history = [item for item in history if not (
                    item.get("tipo") == LEGACY_SOURCE_TYPE
                    and normalize_text(item.get("legacy_source_id")) == normalize_text(case["legacy_source_id"])
                )]
                history.append({
                    "tipo": LEGACY_SOURCE_TYPE,
                    "legacy_source_id": case["legacy_source_id"],
                    "canonical_recipe_id": recipe_id,
                    "accion": "CANONICALIZADO",
                })
                update = sandbox_repo.editar_borrador_incompleto(recipe_id, {
                    "ingredientes_estructurados": structured,
                    "otras_dependencias": sorted(set(dependencies)),
                    "historial_procedencia": history,
                })
                if not update.get("ok"):
                    raise LegacyCanonicalizationError(
                        "dependency_link_failed", "; ".join(update.get("errores") or [])
                    )
            payload = json.loads(target.read_text(encoding="utf-8"))
            transaction = MotorEscrituraSeguraI1342(
                self.base_dir, [RECIPE_PATH]
            ).ejecutar({RECIPE_PATH: payload}, idempotency_key=f"legacy-canonical:{token}")
            if transaction.estado != "COMMIT":
                raise LegacyCanonicalizationError(
                    "transaction_failed", transaction.error or "No se pudo aplicar la canonicalización."
                )
        reread = [self.recipes.obtener(recipe_id) for recipe_id in legacy_to_canonical.values()]
        return {
            "ok": True, "estado": "CONFIRMADO", "recetas": reread,
            "canonicalizadas": len(reread), "idempotente": False,
            "stock_modificado": False, "compras_modificadas": False,
            "datos_reales_modificados": True,
        }

    def _case(self, cost_sheet: Any) -> dict[str, Any]:
        recipe = cost_sheet.receta
        legacy_id = str(recipe.codigo or "")
        linked = self._linked_recipe(legacy_id, self.recipes)
        ingredients = []
        valid_articles = {
            normalize_text(item.get("codigo") or item.get("id"))
            for item in self.products.listar_productos(incluir_archivados=False)
        }
        for item in recipe.ingredientes:
            article_id = str(item.articulo_id or "") or None
            if article_id and normalize_text(article_id) not in valid_articles:
                article_id = None
            metadata = dict(item.metadata or {})
            ingredients.append({
                "nombre": item.nombre, "cantidad": item.cantidad, "unidad": item.unidad,
                "article_id": article_id,
                "legacy_dependency_id": metadata.get("referencia_elaboracion"),
            })
        imported = {
            "nombre": recipe.nombre,
            "ingredientes_estructurados": [
                {"nombre_original": item["nombre"], "article_id": item.get("article_id")}
                for item in ingredients
            ],
        }
        match = CanonicalRecipeMatcher(self.base_dir).match(imported)
        canonical_candidates = [item for item in match.get("candidatos") or [] if (
            item.get("tipo") != "ESCANDALLO_SIN_RECETA_CANONICA"
        )]
        if linked:
            state, action = "REUTILIZAR_EXISTENTE_CANONICA", "REUTILIZAR_EXISTENTE"
            canonical_id = linked["id"]
        elif match.get("accion") == "REUTILIZAR_EXISTENTE" and canonical_candidates:
            state, action = "REUTILIZAR_EXISTENTE_CANONICA", "ENLAZAR_EXISTENTE"
            canonical_id = match.get("entidad_existente_id")
        elif canonical_candidates:
            state, action = "POSIBLE_VARIANTE", "REQUIERE_DECISION"
            canonical_id = None
        elif recipe.nombre and ingredients:
            state, action = LEGACY_WITHOUT_CANONICAL, "CANONICALIZAR"
            canonical_id = None
        else:
            state, action = "EVIDENCIA_INSUFICIENTE", "REQUIERE_DECISION"
            canonical_id = None
        return {
            "legacy_source_type": LEGACY_SOURCE_TYPE,
            "legacy_source_id": legacy_id, "nombre": recipe.nombre,
            "estado": state, "accion_propuesta": action,
            "canonical_recipe_id": canonical_id,
            "ingredientes": ingredients, "rendimiento": recipe.rendimiento,
            "unidad_rendimiento": recipe.unidad_rendimiento,
            "coste_total_legacy": cost_sheet.coste_total,
            "evidencia": "ID legacy + nombre + estructura completa del escandallo 555A",
            "candidatos_canonicos": canonical_candidates,
        }

    def _recipe_payload(
        self, case: dict[str, Any], legacy_to_canonical: dict[str, str]
    ) -> dict[str, Any]:
        ingredients = list(case["ingredientes"])
        quantities = [f"{item['cantidad']} {item['unidad']}".strip() for item in ingredients]
        return {
            "nombre": case["nombre"], "tipo": "PRINCIPAL",
            "numero_raciones": case.get("rendimiento") or 0,
            "ingredientes": [item["nombre"] for item in ingredients],
            "cantidades": quantities, "elaboracion": "",
            "ingredientes_estructurados": [{
                "nombre_original": item["nombre"], "article_id": item.get("article_id"),
                "elaboracion_id": legacy_to_canonical.get(normalize_text(item.get("legacy_dependency_id"))),
                "cantidad": item.get("cantidad"), "unidad": item.get("unidad"),
            } for item in ingredients],
            "coste_total": str(case.get("coste_total_legacy") or ""),
            "precio": "", "coste_por_racion": "",
            "notas_documentacion": "Canonicalizada desde escandallo legacy 555A; procedimiento no disponible.",
            "procedencia_campos": {
                field: {"tipo": "LEGACY", "legacy_source_type": LEGACY_SOURCE_TYPE,
                        "legacy_source_id": case["legacy_source_id"]}
                for field in ("nombre", "ingredientes", "numero_raciones", "coste_total")
            },
            "historial_procedencia": [{
                "tipo": LEGACY_SOURCE_TYPE, "legacy_source_id": case["legacy_source_id"],
                "accion": "CANONICALIZACION_PREPARADA",
            }],
        }

    def _linked_recipe(
        self, legacy_id: str, repository: RepositorioBibliotecaRecetas601
    ) -> dict[str, Any] | None:
        key = normalize_text(legacy_id)
        for recipe in repository.listar(incluir_archivadas=True):
            for item in recipe.get("historial_procedencia") or []:
                if item.get("tipo") == LEGACY_SOURCE_TYPE and normalize_text(
                    item.get("legacy_source_id")
                ) == key:
                    return recipe
        return None

    @staticmethod
    def _dependency_order(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        remaining = list(cases)
        selected_ids = {
            key for item in remaining
            for key in (normalize_text(item["legacy_source_id"]), normalize_text(item["nombre"]))
        }
        ordered: list[dict[str, Any]] = []
        resolved: set[str] = set()
        while remaining:
            ready = [case for case in remaining if {
                normalize_text(item.get("legacy_dependency_id"))
                for item in case["ingredientes"] if normalize_text(item.get("legacy_dependency_id"))
            }.intersection(selected_ids) <= resolved]
            if not ready:  # Ciclo legacy: se crean primero y se enlazan en segunda pasada.
                ready = [remaining[0]]
            for case in ready:
                ordered.append(case); remaining.remove(case)
                resolved.add(normalize_text(case["legacy_source_id"]))
                resolved.add(normalize_text(case["nombre"]))
        return ordered

    def _fingerprint(self) -> str:
        digest = hashlib.sha256()
        for path in (self.recipes.path, self.legacy.ruta):
            digest.update(path.read_bytes() if path.exists() else b"")
        return digest.hexdigest()

    @staticmethod
    def _actor(context: AuthorizedExecutionContext) -> tuple[str, str]:
        return context.user_id, context.tenant_id

    @staticmethod
    def _authorize(context: AuthorizedExecutionContext, *, write: bool) -> None:
        valid, reason = context.validate()
        scope = "recetas:write" if write else "recetas:preview"
        if not valid or scope not in context.scopes:
            raise LegacyCanonicalizationError("forbidden", reason or f"Falta scope {scope}.")


__all__ = [
    "LEGACY_WITHOUT_CANONICAL", "LegacyCanonicalizationError",
    "LegacyRecipeCanonicalizationService",
]
