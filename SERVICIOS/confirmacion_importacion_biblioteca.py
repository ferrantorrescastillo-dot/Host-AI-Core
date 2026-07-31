from __future__ import annotations

import json
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


STORE_PATH = "DATOS/db/biblioteca_importaciones_web.json"
DOMAIN_PATHS = (
    "DATOS/db/articulos.json",
    "DATOS/db/biblioteca_recetas_601.json",
    "DATOS/db/biblioteca_escandallos_601.json",
    "DATOS/db/proveedores.json",
    "DATOS/db/compras_producto_proveedor.json",
    "DATOS/facturas/historico_precios.json",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ImportSessionRepository:
    """Persistencia estructurada de sesiones; nunca conserva el documento original."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.path = self.base_dir / STORE_PATH

    def load_all(self) -> dict[str, dict[str, Any]]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}
        sessions = payload.get("sesiones") if isinstance(payload, dict) else {}
        return deepcopy(sessions) if isinstance(sessions, dict) else {}

    def save_all(self, sessions: dict[str, dict[str, Any]]) -> None:
        motor = MotorEscrituraSeguraI1342(self.base_dir, [STORE_PATH])
        result = motor.ejecutar({STORE_PATH: {"version": 1, "sesiones": sessions}})
        if result.estado != "COMMIT":
            raise RuntimeError(result.error or "No se pudo persistir la importación.")


class ImportConfirmationService:
    def __init__(self, base_dir: Path, repository: ImportSessionRepository) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.repository = repository

    def preflight(self, session: dict[str, Any], version: int) -> list[dict[str, Any]]:
        draft = ImportDraftService(self.base_dir).validate(
            dict(session.get("borrador") or {})
        )
        errors: list[dict[str, Any]] = []
        if int(draft.get("version") or 0) != version:
            errors.append(self._issue(
                "VERSION_CONFLICT", "borrador",
                "La versión revisada ya no es la actual.", field="version",
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
        )
        return errors

    def confirm(
        self, sessions: dict[str, dict[str, Any]], import_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        session = sessions[import_id]
        version = int(payload.get("draft_version") or 0)
        user = str(payload.get("usuario") or "").strip()
        if str(payload.get("confirmacion") or "") != "CONFIRMAR" or not user:
            return self._error("confirmation_required", "Se requiere confirmación explícita y usuario.", 400)
        errors = self.preflight(session, version)
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
            actions: list[dict[str, Any]] = []
            entities: list[dict[str, Any]] = []
            for item in session["borrador"]["recipes"]:
                if item.get("entity_type") == "DESCARTAR" or item.get("proposed_action") == "IGNORAR":
                    continue
                ingredients, quantities, lines = [], [], []
                for ingredient in item.get("ingredients") or []:
                    article_id = ingredient.get("article_id")
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
                recipe_payload = {
                    "nombre": item["title"], "ingredientes": ingredients, "cantidades": quantities,
                    "elaboracion": "\n".join(item.get("procedure") or []),
                    "numero_raciones": item.get("servings") or item.get("yield_value"),
                    "tipo": item.get("entity_type"), "descripcion": item.get("description") or "",
                    "observaciones": item.get("notes") or "",
                    "otras_dependencias": [item["parent_recipe_id"]] if item.get("parent_recipe_id") else [],
                    "notas_documentacion": f"Origen estructurado: {session['documento']['nombre']}",
                }
                action = str(item.get("proposed_action") or "")
                existing_id = ""
                candidates = item.get("duplicate_candidates") or []
                if candidates:
                    existing_id = str(candidates[0].get("id") or candidates[0].get("codigo") or "")
                result = recipes.editar(existing_id, recipe_payload) if action.startswith("ACTUALIZAR") else recipes.crear_ficha_tecnica(recipe_payload)
                if not result.get("ok"):
                    raise ValueError("; ".join(result.get("errores") or ["No se pudo guardar la receta."]))
                recipe = result["receta"]
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
            changes: dict[str, Any] = {}
            for rel in DOMAIN_PATHS:
                path = sandbox / rel
                if path.exists():
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
