from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any, Protocol
import uuid

from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.host_ai_engine.models import HostAIEngineRequest
from SERVICIOS.host_ai_engine.service import HostAIEngine


logger = logging.getLogger(__name__)


class RecetaDocumentacionError(ValueError):
    def __init__(self, code: str, message: str): self.code = code; super().__init__(message)


class GeneratedProposals(dict[str, Any]):
    def __init__(self, values: dict[str, Any], diagnostics: dict[str, Any]) -> None:
        super().__init__(values)
        self.diagnostics = diagnostics


class RecipeProposalGenerator(Protocol):
    def generate(self, *, recipe: dict[str, Any], missing_fields: list[str], allowed_fields: set[str]) -> dict[str, Any]: ...


class HostAIRecipeProposalGenerator:
    """Adaptador de generación: usa el provider configurado sin concederle WRITE."""

    def __init__(self, base_dir: Path, engine: HostAIEngine | None = None) -> None:
        self.engine = engine or HostAIEngine(base_dir)

    def generate(self, *, recipe: dict[str, Any], missing_fields: list[str], allowed_fields: set[str], session_id: str = "") -> dict[str, Any]:
        provider = str(self.engine.default_provider or "SIMULADO").upper()
        configured = getattr(self.engine, "_providers", {})
        selected = configured.get(provider)
        if provider == "SIMULADO" or not bool(getattr(selected, "connected", False)):
            provider = next((
                key for key, candidate in configured.items()
                if key != "SIMULADO" and bool(getattr(candidate, "connected", False))
            ), "")
        if not provider:
            raise RecetaDocumentacionError("ai_provider_unavailable", "No hay un proveedor IA productivo configurado para generar propuestas.")
        missing_keys = {
            self.MISSING_FIELD_KEYS.get(str(label).strip().casefold(), "")
            for label in missing_fields
        }
        requested_fields = sorted((missing_keys - {""}) & allowed_fields)
        if not requested_fields:
            diagnostics = {
                "recipe_id": recipe.get("id") or recipe.get("codigo"),
                "pending_fields": list(missing_fields), "requested_fields": [],
                "returned_keys": [], "discarded_keys": [], "final_keys": [],
            }
            logger.info("recipe_ai_proposal_filter %s", json.dumps(diagnostics, ensure_ascii=False, sort_keys=True))
            return GeneratedProposals({}, diagnostics)
        context = {
            "receta_id": recipe.get("id") or recipe.get("codigo"),
            "nombre": recipe.get("nombre"),
            "ingredientes": recipe.get("ingredientes_estructurados") or recipe.get("ingredientes") or [],
            "cantidades": recipe.get("cantidades") or [],
            "datos_existentes": {
                key: recipe.get(key) for key in sorted(allowed_fields)
                if self._present(recipe.get(key))
            },
            "campos_faltantes_proponibles": requested_fields,
        }
        request = HostAIEngineRequest(
            origen="BIBLIOTECA_WEB", modulo="RECETAS_IA", tipo_peticion="completar_campos_faltantes_receta",
            proveedor_preferido=provider,
            datos_enviados={"pregunta": (
                "Devuelve exclusivamente un objeto JSON, sin Markdown, con propuestas culinarias para los campos faltantes. "
                "No incluyas campos existentes ni inventes precio, proveedor, stock, lotes o identificadores. "
                f"Devuelve un JSON plano cuyas unicas claves sean: {requested_fields}. "
                f"Contexto culinario necesario: {json.dumps(context, ensure_ascii=False, sort_keys=True)}"
            )},
            operation_id="RECIPE_AI-" + str(uuid.uuid4()), session_id=session_id, entity_type="RECIPE", entity_id=str(recipe.get("id") or recipe.get("codigo") or ""),
        )
        response = self.engine.ejecutar(request)
        if not response.estado.startswith("OK"):
            safe_errors = [str(item) for item in list(response.errores or [])]
            category = self._error_category(safe_errors)
            logger.warning(
                "recipe_ai_provider_failed request_id=%s provider=%s model=%s category=%s errors=%s",
                response.request_id, response.proveedor, response.modelo, category, safe_errors,
            )
            messages = {
                "timeout": "El proveedor IA no respondio dentro del tiempo permitido.",
                "authentication": "El proveedor IA rechazo la configuracion de acceso.",
                "quota": "El proveedor IA no tiene cuota disponible.",
                "connection": "No se pudo conectar con el proveedor IA.",
            }
            raise RecetaDocumentacionError(f"ai_provider_{category}", messages.get(category, "El proveedor IA no pudo generar propuestas."))
        raw = str((response.respuesta or {}).get("mensaje") or "").strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try: parsed = json.loads(raw)
        except (TypeError, ValueError): raise RecetaDocumentacionError("ai_invalid_response", "El proveedor IA no devolvió propuestas estructuradas válidas.")
        if not isinstance(parsed, dict): raise RecetaDocumentacionError("ai_invalid_response", "La propuesta IA no tiene el formato esperado.")
        final = {key: value for key, value in parsed.items() if key in requested_fields}
        discarded = [{
            "key": str(key),
            "reason": "NOT_ALLOWED" if key not in allowed_fields else "NOT_REQUESTED",
        } for key in parsed if key not in final]
        diagnostics = {
            "recipe_id": recipe.get("id") or recipe.get("codigo"),
            "pending_fields": list(missing_fields), "requested_fields": requested_fields,
            "returned_keys": sorted(str(key) for key in parsed),
            "discarded_keys": discarded, "final_keys": sorted(final),
            "cost_breakdown": dict(getattr(response, "cost_breakdown", {}) or {}),
        }
        logger.info("recipe_ai_proposal_filter %s", json.dumps(diagnostics, ensure_ascii=False, sort_keys=True))
        return GeneratedProposals(final, diagnostics)

    FIELD_LABELS = {
        "descripcion": "Descripción", "elaboracion": "Elaboración paso a paso",
        "tiempo_activo": "Tiempo activo", "tiempo_pasivo": "Tiempo pasivo", "tiempo_total": "Tiempo total",
        "puede_congelarse": "Puede congelarse", "puede_refrigerarse": "Puede refrigerarse",
        "vida_util_refrigerado": "Vida útil refrigerada", "vida_util_congelado": "Vida útil congelada",
        "regeneracion": "Tiempo de regeneración", "observaciones": "Observaciones",
        "alergenos": "Alérgenos", "numero_raciones": "Número de raciones",
    }
    MISSING_FIELD_KEYS = {label.casefold(): key for key, label in FIELD_LABELS.items()}

    @staticmethod
    def _present(value: Any) -> bool:
        return value is not None and value != "" and value != []

    @staticmethod
    def _error_category(errors: list[str]) -> str:
        text = " ".join(errors).casefold()
        if "tiempo" in text or "timeout" in text: return "timeout"
        if "credencial" in text or "permiso" in text or "autentic" in text: return "authentication"
        if "cuota" in text or "credito" in text or "cr\u00e9dito" in text: return "quota"
        if "conectar" in text or "red" in text: return "connection"
        return "provider"


class RecetaDocumentacionWriteService:
    """Aceptación selectiva de propuestas; la generación IA permanece separada del WRITE."""

    REQUIRED_SCOPE = "recetas:write"
    FIELDS = frozenset({"descripcion", "elaboracion", "tiempo_activo", "tiempo_pasivo", "tiempo_total", "puede_congelarse", "puede_refrigerarse", "vida_util_refrigerado", "vida_util_congelado", "regeneracion", "observaciones", "alergenos", "numero_raciones"})
    _lock = RLock()

    def __init__(self, base_dir: Path, repository: RepositorioBibliotecaRecetas601 | None = None, generator: RecipeProposalGenerator | None = None) -> None:
        self.repository = repository or RepositorioBibliotecaRecetas601(base_dir)
        self.generator = generator or HostAIRecipeProposalGenerator(base_dir)
        self._completed: dict[str, dict[str, Any]] = {}

    def proposal(self, *, recipe_id: str, proposed: dict[str, Any], detected_allergens: list[str] | None = None, session_id: str = "") -> dict[str, Any]:
        current = self._recipe(recipe_id)
        required_missing = list((current.get("completitud") or {}).get("campos_obligatorios_pendientes") or [])
        labels_by_key = HostAIRecipeProposalGenerator.FIELD_LABELS
        safe_missing = [labels_by_key[key] for key in sorted(self.FIELDS) if not self._present(current.get(key)) and key in labels_by_key]
        missing = list(dict.fromkeys([*required_missing, *safe_missing]))
        non_proposable = [label for label in required_missing if HostAIRecipeProposalGenerator.MISSING_FIELD_KEYS.get(str(label).strip().casefold()) not in self.FIELDS]
        if not proposed:
            proposed = self.generator.generate(recipe=current, missing_fields=missing, allowed_fields=set(self.FIELDS), session_id=session_id) if isinstance(self.generator, HostAIRecipeProposalGenerator) else self.generator.generate(recipe=current, missing_fields=missing, allowed_fields=set(self.FIELDS))
        clean = {key: value for key, value in dict(proposed or {}).items() if key in self.FIELDS and self._present(value)}
        clean = {key: value for key, value in clean.items() if not self._present(current.get(key))}
        diagnostics = dict(getattr(proposed, "diagnostics", {}) or {})
        discarded = list(diagnostics.get("discarded_keys") or [])
        diagnosed_keys = {str(item.get("key")) for item in discarded if isinstance(item, dict)}
        for key, value in dict(proposed or {}).items():
            if str(key) in diagnosed_keys or key in clean:
                continue
            reason = "NOT_ALLOWED" if key not in self.FIELDS else "EMPTY_VALUE" if not self._present(value) else "EXISTING_VALUE"
            discarded.append({"key": str(key), "reason": reason})
        logger.info(
            "recipe_ai_proposal_result recipe_id=%s pending=%s proposable=%s non_proposable=%s final=%s",
            current.get("id") or current.get("codigo"), required_missing, safe_missing, non_proposable, sorted(clean),
        )
        return {"ok": True, "receta_id": str(current.get("id") or current.get("codigo")), "datos_existentes": {key: current.get(key) for key in self.FIELDS if self._present(current.get(key))}, "datos_propuestos_ia": clean, "campos_faltantes_motor": required_missing, "campos_pendientes_proponibles": safe_missing, "campos_pendientes_no_proponibles": non_proposable, "campos_descartados": discarded, "campos_sin_datos": sorted(key for key in self.FIELDS if not self._present(current.get(key))), "alergenos_detectados_datos": list(detected_allergens or current.get("alergenos") or []), "alergenos_propuestos_ia": list(clean.get("alergenos") or []), "cost_breakdown": dict(diagnostics.get("cost_breakdown") or {}), "generado_ahora": True, "datos_reales_modificados": False}

    def preview(self, *, recipe_id: str, selected: dict[str, Any], overwrite_fields: list[str], context: AuthorizedExecutionContext) -> dict[str, Any]:
        self._authorize(context)
        current = self._recipe(recipe_id)
        changes = self._validate_selection(current, selected, overwrite_fields)
        token = self._token(current, changes, context)
        return {"ok": True, "estado": "LISTO_PARA_CONFIRMAR" if changes else "SIN_CAMBIOS", "receta_antes": current, "cambios_seleccionados": changes, "receta_propuesta": {**current, **changes}, "preview_token": token, "requiere_confirmacion": bool(changes), "datos_reales_modificados": False}

    def confirm(self, *, recipe_id: str, selected: dict[str, Any], overwrite_fields: list[str], preview_token: str, context: AuthorizedExecutionContext) -> dict[str, Any]:
        with self._lock:
            if preview_token in self._completed:
                return {**self._completed[preview_token], "idempotente": True}
            preview = self.preview(recipe_id=recipe_id, selected=selected, overwrite_fields=overwrite_fields, context=context)
            if not preview_token or preview_token != preview["preview_token"]: raise RecetaDocumentacionError("stale_or_invalid_preview", "La vista previa ya no es válida.")
            if not preview["requiere_confirmacion"]: return {**preview, "idempotente": True}
            current = preview["receta_antes"]
            now = datetime.now().isoformat(timespec="seconds")
            origins = dict(current.get("procedencia_campos") or {})
            history = list(current.get("historial_procedencia") or [])
            for field, value in preview["cambios_seleccionados"].items():
                history.append({"campo": field, "valor_anterior": current.get(field), "valor_nuevo": value, "origen_anterior": origins.get(field), "origen_nuevo": "IA", "actor": context.user_id, "timestamp": now, "estado_revision": "PENDIENTE_REVISION"})
                origins[field] = {"tipo": "IA", "actor_id": context.user_id, "fecha": now, "estado_revision": "PENDIENTE_REVISION"}
            result = self.repository.editar(recipe_id, {**preview["cambios_seleccionados"], "procedencia_campos": origins, "historial_procedencia": history})
            if not result.get("ok"): raise RecetaDocumentacionError("write_failed", " | ".join(result.get("errores") or ["No se pudo guardar."]))
            persisted = self._recipe(recipe_id)
            response = {"ok": True, "estado": "CONFIRMADO", "receta": persisted, "campos_confirmados": sorted(preview["cambios_seleccionados"]), "idempotente": False, "datos_reales_modificados": True, "lectura_posterior_verificada": all(persisted.get(key) == value for key, value in preview["cambios_seleccionados"].items())}
            self._completed[preview_token] = response
            return response

    def _validate_selection(self, current: dict[str, Any], selected: dict[str, Any], overwrite_fields: list[str]) -> dict[str, Any]:
        overwrites = set(overwrite_fields or [])
        changes = {}
        for key, value in dict(selected or {}).items():
            if key not in self.FIELDS: raise RecetaDocumentacionError("unsupported_field", f"Campo no admitido: {key}.")
            if not self._present(value): continue
            if self._present(current.get(key)) and current.get(key) != value and key not in overwrites:
                raise RecetaDocumentacionError("overwrite_confirmation_required", f"El campo {key} ya contiene datos.")
            if current.get(key) != value: changes[key] = value
        return changes

    def _recipe(self, identity: str) -> dict[str, Any]:
        recipe = self.repository.obtener(str(identity or "").strip())
        if not recipe: raise RecetaDocumentacionError("recipe_not_found", "Receta no encontrada.")
        return recipe

    def _authorize(self, context: AuthorizedExecutionContext) -> None:
        valid, _ = context.validate() if isinstance(context, AuthorizedExecutionContext) else (False, "")
        if not valid or self.REQUIRED_SCOPE not in context.scopes: raise RecetaDocumentacionError("unauthorized", "El actor no está autorizado.")

    @staticmethod
    def _present(value: Any) -> bool: return value is not None and value != "" and value != []

    @staticmethod
    def _token(current: dict[str, Any], changes: dict[str, Any], context: AuthorizedExecutionContext) -> str:
        raw = json.dumps({"current": current, "changes": changes, "actor": context.user_id, "tenant": context.tenant_id}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()


__all__ = ["RecetaDocumentacionWriteService", "RecetaDocumentacionError", "RecipeProposalGenerator", "HostAIRecipeProposalGenerator"]
