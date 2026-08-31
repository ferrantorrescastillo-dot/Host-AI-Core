from __future__ import annotations

import json
import hashlib
import shutil
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from SERVICIOS.biblioteca_escandallos_601 import BibliotecaEscandallos601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.borrador_importacion_biblioteca import ImportDraftService
from SERVICIOS.motor_escritura_segura_i1342 import MotorEscrituraSeguraI1342
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601
from SERVICIOS.borrador_importacion_biblioteca import normalize_text
from SERVICIOS.biblioteca_menus_601 import RepositorioBibliotecaMenus601
from SERVICIOS.menu_importacion_biblioteca import apply_menu_imports
from SERVICIOS.repository_initialization_policy import non_persistent_repository_initialization


STORE_PATH = "DATOS/db/biblioteca_importaciones_web.json"
DOMAIN_PATHS = (
    "DATOS/db/articulos.json",
    "DATOS/db/biblioteca_recetas_601.json",
    "DATOS/db/biblioteca_escandallos_601.json",
    "DATOS/db/proveedores.json",
    "DATOS/db/compras_producto_proveedor.json",
    "DATOS/facturas/historico_precios.json",
    "DATOS/db/menus.json",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ImportSessionRepository:
    """Persistencia estructurada de sesiones; nunca conserva el documento original."""

    def __init__(self, base_dir: Path, *, persistent: bool = True) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.path = self.base_dir / STORE_PATH
        self.persistent = persistent

    def load_all(self) -> dict[str, dict[str, Any]]:
        if not self.persistent:
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}
        sessions = payload.get("sesiones") if isinstance(payload, dict) else {}
        return deepcopy(sessions) if isinstance(sessions, dict) else {}

    def save_all(self, sessions: dict[str, dict[str, Any]]) -> None:
        if not self.persistent:
            return
        motor = MotorEscrituraSeguraI1342(self.base_dir, [STORE_PATH])
        result = motor.ejecutar({STORE_PATH: {"version": 1, "sesiones": sessions}})
        if result.estado != "COMMIT":
            raise RuntimeError(result.error or "No se pudo persistir la importación.")


class ImportConfirmationService:
    def __init__(self, base_dir: Path, repository: ImportSessionRepository) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.repository = repository

    @staticmethod
    def _draft_fingerprint(draft: dict[str, Any]) -> str:
        return hashlib.sha256(
            json.dumps(draft, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()

    def preflight(
        self, session: dict[str, Any], version: int, preview_fingerprint: str = "",
    ) -> list[dict[str, Any]]:
        draft = ImportDraftService(self.base_dir, initialize_matchers=False).validate(
            dict(session.get("borrador") or {})
        )
        errors: list[dict[str, Any]] = []
        if int(draft.get("version") or 0) != version:
            errors.append(self._issue(
                "VERSION_CONFLICT", "borrador",
                "La versión revisada ya no es la actual.", field="version",
            ))
        if preview_fingerprint and self._draft_fingerprint(draft) != preview_fingerprint:
            errors.append(self._issue(
                "PREVIEW_OBSOLETO", "borrador",
                "El borrador ya no coincide con la previsualización revisada.", field="preview_fingerprint",
            ))
        if str(session.get("estado") or "") == "CONFIRMADA":
            errors.append(self._issue("IMPORT_ALREADY_CONFIRMED", "importación", "La importación ya fue confirmada."))
        errors.extend(
            self._issue(
                str(issue["code"]),
                str(issue.get("ingredient_id") or issue.get("recipe_id") or "borrador"),
                str(issue["message"]),
                level=str(issue.get("level") or "BLOQUEANTE"),
                recipe_id=issue.get("recipe_id"),
                recipe_title=issue.get("recipe_title"),
                recipe_index=issue.get("recipe_index"),
                ingredient_id=issue.get("ingredient_id"),
                ingredient_index=issue.get("ingredient_index"),
                field=str(issue.get("field") or ""),
            )
            for issue in draft.get("validation", {}).get("blocking_errors", [])
            if str(issue.get("code") or "") != "RECETA_REQUIERE_REVISION"
        )
        # Los elementos de catálogo pendientes quedan fuera de la transacción; nunca se crean ni reutilizan.
        return errors

    def confirm(
        self, sessions: dict[str, dict[str, Any]], import_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        session = sessions[import_id]
        version = int(payload.get("draft_version") or 0)
        user = str(payload.get("usuario") or "").strip()
        if str(payload.get("confirmacion") or "") != "CONFIRMAR" or not user:
            return self._error("confirmation_required", "Se requiere confirmación explícita y usuario.", 400)
        errors = self.preflight(session, version, str(payload.get("preview_fingerprint") or ""))
        if errors:
            return self._failure("validation_failed", "El borrador contiene errores bloqueantes.", errors)

        before = deepcopy(session)
        try:
            changes, actions, entities = self._prepare_domain_changes(session)
            updated = deepcopy(session)
            updated["estado"] = "CONFIRMADA"
            updated["confirmacion_disponible"] = False
            updated["solo_previsualizacion"] = False
            updated["confirmada_en"] = _now()
            updated["confirmada_por"] = user
            report = {
                "estado": "COMPLETADA",
                "acciones": actions,
                "entidades": entities,
                "errores": [],
                "rollback": False,
            }
            updated["resultado_confirmacion"] = report
            updated.setdefault("historial", []).append({
                "fecha": updated["confirmada_en"], "usuario": user, "version": version,
                "resultado": "COMPLETADA", "acciones": actions, "entidades": entities,
                "errores": [], "rollback": False,
            })
            candidate_sessions = deepcopy(sessions)
            candidate_sessions[import_id] = updated
            changes[STORE_PATH] = {"version": 1, "sesiones": candidate_sessions}
            motor = MotorEscrituraSeguraI1342(
                self.base_dir, list(changes)
            )
            transaction = motor.ejecutar(
                changes, idempotency_key=f"biblioteca-import-{import_id}-v{version}"
            )
            if transaction.estado != "COMMIT":
                raise RuntimeError(transaction.error or "La transacción fue revertida.")
            sessions.clear()
            sessions.update(candidate_sessions)
            report["transaccion_id"] = transaction.transaccion_id
            with non_persistent_repository_initialization():
                menu_repo = RepositorioBibliotecaMenus601(self.base_dir)
            verified_menus = []
            for entity in entities:
                if entity.get("tipo") not in {"MENU", "MENU_EXISTENTE"}:
                    continue
                persisted = menu_repo.obtener(str(entity.get("id") or ""))
                if not persisted:
                    raise RuntimeError(f"El menú {entity.get('id')} no aparece en la lectura post-write.")
                verified_menus.append({
                    "menu_id": persisted.get("menu_id"), "nombre": persisted.get("nombre"),
                    "lineas": sum(len(lines or []) for lines in dict(persisted.get("composicion") or {}).values()),
                    "referencias": [
                        line.get("referencia")
                        for lines in dict(persisted.get("composicion") or {}).values()
                        for line in lines or []
                    ],
                })
            report["verificacion_post_write"] = {"menus": verified_menus, "total": len(verified_menus)}
            return {"ok": True, "importacion_id": import_id, "estado": "CONFIRMADA", "resultado": report}
        except Exception as exc:
            sessions[import_id] = before
            failure = {
                "fecha": _now(), "usuario": user, "version": version, "resultado": "FALLIDA",
                "acciones": [], "entidades": [], "errores": [{
                    "entidad": import_id, "validacion": type(exc).__name__,
                    "accion": "confirmar_importacion", "mensaje": str(exc),
                }], "rollback": True,
            }
            # El historial del fallo se persiste fuera de la transacción de dominio.
            sessions[import_id].setdefault("historial", []).append(failure)
            self.repository.save_all(sessions)
            return self._failure("confirmation_failed", "La confirmación fue revertida.", failure["errores"])

    def _prepare_domain_changes(
        self, session: dict[str, Any]
    ) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
        with tempfile.TemporaryDirectory(prefix="hostai-import-") as temp:
            sandbox = Path(temp)
            for rel in DOMAIN_PATHS:
                source, target = self.base_dir / rel, sandbox / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                if source.exists():
                    shutil.copy2(source, target)
            recipes = RepositorioBibliotecaRecetas601(sandbox)
            products = RepositorioProductosMaestro601(sandbox)
            escandallos = BibliotecaEscandallos601(sandbox)
            baseline = {
                rel: (sandbox / rel).read_bytes()
                for rel in DOMAIN_PATHS if (sandbox / rel).exists()
            }
            actions: list[dict[str, Any]] = []
            entities: list[dict[str, Any]] = []
            catalog = dict(session.get("borrador", {}).get("catalogo") or {})
            supplier_ids: dict[str, str] = {}
            existing_suppliers = {
                normalize_text(item.get("nombre")): item
                for item in products.listar_proveedores()
            }
            for item in catalog.get("proveedores") or []:
                key = normalize_text(item.get("nombre"))
                existing = existing_suppliers.get(key)
                if item.get("accion") == "REUTILIZAR":
                    if not existing:
                        raise ValueError(f"Proveedor a reutilizar no encontrado: {item.get('nombre')}.")
                    supplier = existing
                elif item.get("accion") == "CREAR":
                    provenance = json.dumps(item.get("origen") or {}, ensure_ascii=False, sort_keys=True)
                    supplier = products.crear_proveedor({
                        "nombre": item.get("nombre"),
                        "observaciones": f"Confirmado por importación {session['documento']['id']}. Origen: {provenance}",
                    })
                    actions.append({"tipo": "CREAR_PROVEEDOR", "id": supplier["codigo"]})
                    entities.append({"tipo": "PROVEEDOR", "id": supplier["codigo"], "nombre": supplier["nombre"]})
                else:
                    continue
                supplier_ids[key] = str(supplier.get("codigo") or "")

            article_ids: dict[str, str] = {}
            for item in catalog.get("articulos") or []:
                action = str(item.get("accion") or "")
                if action == "REUTILIZAR":
                    article = products.obtener_producto(str(item.get("article_id") or ""))
                    if not article:
                        raise ValueError(f"Artículo a reutilizar no encontrado: {item.get('nombre')}.")
                elif action == "CREAR":
                    provenance = json.dumps(item.get("origen") or {}, ensure_ascii=False, sort_keys=True)
                    article = products.crear_producto({
                        "nombre": item.get("nombre"),
                        "tipo_entidad": "ARTICULO_COMPRADO",
                        "proveedor": item.get("proveedor") or "",
                        "unidad_compra": item.get("formato") or "",
                        "observaciones": f"Confirmado por importación {session['documento']['id']}. Origen: {provenance}",
                    })
                    actions.append({"tipo": "CREAR_ARTICULO", "id": article["codigo"]})
                    entities.append({"tipo": "ARTICULO", "id": article["codigo"], "nombre": article["nombre"]})
                else:
                    continue
                article_id = str(article.get("codigo") or article.get("id") or "")
                article_ids[normalize_text(item.get("nombre"))] = article_id

            article_drafts = {item.get("id"): item for item in catalog.get("articulos") or []}
            for relation in catalog.get("relaciones") or []:
                if relation.get("accion") != "CREAR":
                    continue
                article_draft = article_drafts.get(relation.get("articulo_draft_id")) or {}
                article_id = article_ids.get(normalize_text(article_draft.get("nombre")))
                if not article_id:
                    raise ValueError("No se pudo resolver el artículo de la relación con proveedor.")
                products.editar_producto(article_id, {
                    "proveedor": relation.get("proveedor"),
                    "proveedor_preferente": relation.get("proveedor"),
                })
                actions.append({
                    "tipo": "RELACIONAR_ARTICULO_PROVEEDOR", "id": article_id,
                    "proveedor_id": supplier_ids.get(normalize_text(relation.get("proveedor"))),
                })
            recipe_ids: dict[str, str] = {}
            for item in session["borrador"]["recipes"]:
                if item.get("proposed_action") != "REUTILIZAR_EXISTENTE":
                    continue
                candidates = item.get("duplicate_candidates") or []
                existing_id = str(
                    (candidates[0] if candidates else {}).get("id")
                    or (candidates[0] if candidates else {}).get("codigo") or ""
                )
                existing = recipes.obtener(existing_id)
                if not existing:
                    raise ValueError(
                        f"Receta a reutilizar no encontrada: {item.get('title')}."
                    )
                recipe_ids[normalize_text(item.get("title"))] = str(existing["id"])
                actions.append({"tipo": "REUTILIZAR_RECETA", "id": existing["id"]})
                entities.append({
                    "tipo": "RECETA_EXISTENTE", "id": existing["id"],
                    "nombre": existing["nombre"],
                })
            for item in session["borrador"]["recipes"]:
                if item.get("entity_type") == "DESCARTAR" or item.get("proposed_action") == "IGNORAR":
                    continue
                if item.get("proposed_action") in {"REUTILIZAR_EXISTENTE", "SIN_CAMBIOS"}:
                    continue
                if item.get("proposed_action") == "REQUIERE_REVISION":
                    continue
                ingredients, quantities, lines, structured_ingredients = [], [], [], []
                elaboration_dependencies: list[str] = []
                for ingredient in item.get("ingredients") or []:
                    article_id = ingredient.get("article_id")
                    if not article_id:
                        article_id = article_ids.get(normalize_text(ingredient.get("name_raw")))
                    if ingredient.get("relation_status") == "CREAR_ARTICULO_PROPUESTO":
                        product = products.crear_producto({
                            "nombre": ingredient["name_raw"],
                            "unidad_base": ingredient.get("unit") or ingredient.get("unit_raw") or "",
                            "observaciones": f"Propuesto por importación {session['documento']['id']}.",
                        })
                        article_id = product["codigo"]
                        actions.append({"tipo": "CREAR_ARTICULO", "id": article_id})
                    product = products.obtener_producto(str(article_id)) if article_id else None
                    display = str((product or {}).get("nombre") or ingredient.get("name_raw") or "")
                    elaboration_id = recipe_ids.get(normalize_text(ingredient.get("name_raw")))
                    if elaboration_id:
                        elaboration_dependencies.append(elaboration_id)
                    ingredients.append(display)
                    quantities.append(" ".join(filter(None, (
                        str(ingredient.get("quantity_raw") or ingredient.get("quantity") or ""),
                        str(ingredient.get("unit") or ingredient.get("unit_raw") or ""),
                    ))))
                    lines.append({
                        "producto_codigo": str((product or {}).get("codigo") or ""),
                        "producto": display,
                        "cantidad_neta": ingredient.get("quantity"),
                        "unidad_receta": ingredient.get("unit") or ingredient.get("unit_raw") or "",
                        "observaciones": ingredient.get("observations") or "",
                    })
                    structured_ingredients.append({
                        "nombre_original": display,
                        "article_id": str((product or {}).get("codigo") or "") or None,
                        "elaboracion_id": elaboration_id,
                        "cantidad": ingredient.get("quantity"),
                        "cantidad_texto": ingredient.get("quantity_raw"),
                        "unidad": ingredient.get("unit") or ingredient.get("unit_raw") or "",
                    })
                recipe_payload = {
                    "nombre": item["title"], "ingredientes": ingredients, "cantidades": quantities,
                    "elaboracion": "\n".join(item.get("procedure") or []),
                    "numero_raciones": item.get("servings") or item.get("yield_value"),
                    "tipo": item.get("entity_type"), "descripcion": item.get("description") or "",
                    "observaciones": item.get("notes") or "",
                    "ingredientes_estructurados": structured_ingredients,
                    "otras_dependencias": elaboration_dependencies,
                    "notas_documentacion": f"Origen estructurado: {session['documento']['nombre']}",
                    "historial_procedencia": [{
                        "origen": "IMPORTADO", "importacion_id": session["documento"]["id"],
                        "fuente": session["documento"].get("origen"), "bloque": block,
                    } for block in item.get("source_blocks") or []],
                }
                action = str(item.get("proposed_action") or "")
                existing_id = ""
                candidates = item.get("duplicate_candidates") or []
                if candidates:
                    existing_id = str(candidates[0].get("id") or candidates[0].get("codigo") or "")
                # Una importación nunca reemplaza silenciosamente campos humanos.
                # Las actualizaciones requieren una decisión explícita distinta de este flujo.
                if action.startswith("ACTUALIZAR"):
                    raise ValueError(
                        f"La actualización de {item.get('title')} requiere revisar diferencias y autorizar campos."
                    )
                incomplete = not recipe_payload["elaboracion"] or not recipe_payload["numero_raciones"]
                result = (
                    recipes.crear_incompleta_desde_importacion(recipe_payload)
                    if incomplete else recipes.crear_ficha_tecnica(recipe_payload)
                )
                if not result.get("ok"):
                    raise ValueError("; ".join(result.get("errores") or ["No se pudo guardar la receta."]))
                recipe = result["receta"]
                recipe_ids[normalize_text(recipe["nombre"])] = str(recipe["id"])
                actions.append({"tipo": action or "CREAR_RECETA", "id": recipe["id"]})
                entities.append({"tipo": "RECETA", "id": recipe["id"], "nombre": recipe["nombre"]})
                if lines and all(line["producto_codigo"] for line in lines):
                    esc_result = escandallos.crear_manual({
                        "nombre": recipe["nombre"], "numero_raciones": recipe["numero_raciones"],
                        "lineas": lines, "receta_asociada_id": recipe["id"],
                        "receta_asociada_codigo": recipe["codigo"],
                        "receta_asociada_nombre": recipe["nombre"],
                        "receta_asociada_version": recipe["version"],
                    })
                    actions.append({"tipo": "CREAR_ESCANDALLO", "id": esc_result["escandallo"]["id"]})
            menu_actions, menu_entities = apply_menu_imports(
                sandbox,
                dict(session.get("preview_global", {}).get("menus") or {}),
                recipe_ids,
                str(session.get("documento", {}).get("id") or ""),
            )
            actions.extend(menu_actions)
            entities.extend(menu_entities)
            changes: dict[str, Any] = {}
            for rel in DOMAIN_PATHS:
                path = sandbox / rel
                if path.exists() and path.read_bytes() != baseline.get(rel):
                    changes[rel] = json.loads(path.read_text(encoding="utf-8"))
            return changes, actions, entities

    @staticmethod
    def _issue(
        code: str, entity: str, message: str, *, level: str = "BLOQUEANTE",
        recipe_id: Any = None, recipe_title: Any = None, recipe_index: Any = None,
        ingredient_id: Any = None, ingredient_index: Any = None, field: str = "",
    ) -> dict[str, Any]:
        return {
            "code": code,
            "level": level,
            "recipe_id": recipe_id,
            "recipe_title": recipe_title,
            "recipe_index": recipe_index,
            "ingredient_id": ingredient_id,
            "ingredient_index": ingredient_index,
            "field": field,
            "message": message,
            # Alias históricos para consumidores existentes.
            "entidad": entity,
            "validacion": code,
            "accion": "confirmar",
            "mensaje": message,
        }

    @staticmethod
    def _error(code: str, message: str, status: int) -> dict[str, Any]:
        return {"ok": False, "error": {"code": code, "message": message, "status": status}}

    def _failure(self, code: str, message: str, errors: list[dict[str, Any]]) -> dict[str, Any]:
        return {**self._error(code, message, 409), "resultado": {
            "estado": "FALLIDA", "acciones": [], "entidades": [], "errores": errors, "rollback": True,
        }}
