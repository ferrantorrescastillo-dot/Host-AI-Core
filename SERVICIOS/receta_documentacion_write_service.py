from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any, Protocol
import uuid
from copy import deepcopy

from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.host_ai_engine.models import HostAIEngineRequest
from SERVICIOS.host_ai_engine.service import HostAIEngine
from SERVICIOS.recipe_completion_contract import (
    BATCH_GROUP_REVIEW_FIELDS,
    BATCH_INDIVIDUAL_REVIEW_FIELDS,
    BATCH_MASS_SAFE_FIELDS,
    FIELD_CONTRACTS,
    NO_APLICA_FIELDS,
    PRODUCTION_READINESS_BASE_FIELDS,
    PRODUCTION_READINESS_CONDITIONAL_FIELDS,
    RECIPE_BOOLEAN_FIELDS,
    RECIPE_DOCUMENTATION_FIELDS,
    RECIPE_ENUM_FIELDS,
    RECIPE_INGREDIENT_UNITS,
    RECIPE_JSON_FIELDS,
    RECIPE_NUMBER_FIELDS,
    RECIPE_OPERATIONAL_UNITS,
    RECIPE_TIME_FIELDS,
    RECIPE_UNIT_FIELDS,
)


logger = logging.getLogger(__name__)


NO_APLICA_VALUE = {"estado": "NO_APLICA"}


def is_no_aplica(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().upper() == "NO_APLICA"
    return isinstance(value, dict) and str(value.get("estado") or "").strip().upper() == "NO_APLICA"


def classify_recipe_proposals(proposals: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    values = dict(proposals or {})
    return (
        {key: value for key, value in values.items() if key in BATCH_MASS_SAFE_FIELDS},
        {key: value for key, value in values.items() if key not in BATCH_MASS_SAFE_FIELDS},
    )


def classify_recipe_proposals_for_review(
    proposals: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Separa selecciÃ³n segura, revisiÃ³n operativa agrupable y crÃ­tica individual."""
    values = dict(proposals or {})
    return (
        {key: value for key, value in values.items() if key in BATCH_MASS_SAFE_FIELDS},
        {key: value for key, value in values.items() if key in BATCH_GROUP_REVIEW_FIELDS},
        {key: value for key, value in values.items() if key in BATCH_INDIVIDUAL_REVIEW_FIELDS},
    )


def recipe_completion_fingerprint(recipe: dict[str, Any]) -> str:
    keys = sorted(RECIPE_DOCUMENTATION_FIELDS | {
        "id", "codigo", "nombre", "version", "actualizado_en", "ingredientes",
        "ingredientes_estructurados", "cantidades", "completitud",
    })
    payload = {key: recipe.get(key) for key in keys}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


PROPOSAL_ORIGINS = frozenset({
    "DOCUMENTO", "REAL", "CALCULADO", "CONTEXTO_INTERNO", "IA_PROPUESTA",
    "REFERENCIA_EXTERNA", "CONFIRMADO",
})


def proposal_metadata(
    *, origin: str = "IA_PROPUESTA", confidence: float | None = None,
    reason: str = "", source: str = "", url: str = "", model: str = "",
) -> dict[str, Any]:
    normalized = str(origin or "IA_PROPUESTA").strip().upper()
    if normalized not in PROPOSAL_ORIGINS:
        normalized = "IA_PROPUESTA"
    return {
        "origen": normalized,
        "confianza": confidence,
        "motivo": str(reason or ""),
        "fuente": str(source or ""),
        "url": str(url or ""),
        "modelo": str(model or ""),
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "estado_revision": "REQUIERE_REVISION_HUMANA",
    }


def critical_free_text_findings(field: str, value: Any) -> list[str]:
    """Detecta solo afirmaciones criticas con marcadores explicitos y verificables.

    No intenta interpretar la cocina completa ni recortar frases: ante una
    coincidencia de alta confianza, el campo entero se separa para revision.
    """
    if field not in BATCH_MASS_SAFE_FIELDS or not isinstance(value, str):
        return []
    text = "".join(
        character for character in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(character)
    )
    patterns = (
        ("RENDIMIENTO_EMBEBIDO", r"\b(?:rinde|rendimiento|para)\s+(?:unas?\s+)?\d+(?:[.,]\d+)?\s*(?:raciones?|porciones?|pax|personas?)\b"),
        ("VIDA_UTIL_EMBEBIDA", r"\b(?:vida\s+util|caducidad|consumir\s+en\s+\d+|conservar\s+(?:durante|hasta)\s+\d+|\d+\s*(?:horas?|dias?|semanas?|meses?)\s+(?:a|en)\s+(?:[^.\n]{0,12})?(?:refrigeracion|nevera|frio|[^a-z0-9\s]?\s*\d{1,2}\s*[^a-z0-9\s]?\s*c))\b"),
        ("TEMPERATURA_SEGURIDAD_EMBEBIDA", r"\b(?:temperatura\s+interna|alcan(?:z|c)[a-z]*|mantener|conservar)\b[^.\n]{0,48}\b\d{1,3}\s*[^a-z0-9\s]?\s*c\b"),
        ("HACCP_SANITARIO_EMBEBIDO", r"\b(?:haccp|appcc|seguridad\s+alimentaria|criterio\s+sanitario|requisito\s+sanitario)\b"),
        ("ALERGENOS_TRAZAS_EMBEBIDOS", r"\b(?:trazas\s+de|puede\s+contener|contiene\s+(?:los\s+)?alergenos?|declaracion\s+de\s+alergenos?)\b"),
        ("DATOS_COMERCIALES_EMBEBIDOS", r"\b(?:precio\s+(?:de\s+)?compra|coste\s+(?:unitario|total)|stock\s+disponible|proveedor|numero\s+de\s+lote|lote\s+[a-z-]*\d[a-z0-9-]*)\b"),
    )
    findings = [code for code, pattern in patterns if re.search(pattern, text, flags=re.IGNORECASE)]
    return list(dict.fromkeys(findings))


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
        self.base_dir = Path(base_dir).resolve()
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
        completion_context = dict(recipe.get("_contexto_completado") or {})
        context = {
            "receta_id": recipe.get("id") or recipe.get("codigo"),
            "nombre": recipe.get("nombre"),
            "categoria": recipe.get("categoria") or recipe.get("familia"),
            "ingredientes": recipe.get("ingredientes_estructurados") or recipe.get("ingredientes") or [],
            "cantidades": recipe.get("cantidades") or [],
            "texto_original": completion_context.get("texto_original"),
            "procedencia_documental": completion_context.get("procedencia_documental"),
            "articulos_relacionados": completion_context.get("articulos_relacionados") or [],
            "menus": completion_context.get("menus") or [],
            "contexto_servicio": completion_context.get("contexto_servicio") or [],
            "otros_usos": completion_context.get("otros_usos") or [],
            "campos_confirmados": completion_context.get("campos_confirmados") or {},
            "propuestas_previas": completion_context.get("propuestas_previas") or {},
            "datos_existentes": {
                key: recipe.get(key) for key in sorted(allowed_fields)
                if self._present(recipe.get(key))
            },
            "campos_faltantes_proponibles": requested_fields,
            "restricciones_politica": {
                "solo_propuestas": True,
                "sin_write": True,
                "no_sobrescribir_existentes": True,
                "criticos_requieren_revision_humana": True,
                "ingredientes_no_se_pueden_anadir": True,
                "articulos_no_se_crean_desde_este_flujo": True,
            },
        }
        request = HostAIEngineRequest(
            origen="BIBLIOTECA_WEB", modulo="RECETAS_IA", tipo_peticion="completar_campos_faltantes_receta",
            proveedor_preferido=provider,
            datos_enviados={"pregunta": (
                "Devuelve exclusivamente un objeto JSON, sin Markdown, con propuestas culinarias para los campos faltantes. "
                "No incluyas campos existentes ni inventes precio real, proveedor real, stock, lotes o identificadores. "
                "No insertes en descripcion, elaboracion u observaciones rendimientos/raciones, alergenos o trazas, "
                "vida util, conservacion sanitaria, temperaturas internas de seguridad, afirmaciones HACCP, costes, "
                "stock, proveedores ni lotes. No agregues ingredientes que no aparezcan en el contexto aportado. "
                "Propón los campos críticos en su clave estructurada aunque requieran revisión humana. "
                "Para ingredientes_estructurados conserva exactamente el número y orden de ingredientes, y propón "
                "cantidad, unidad, cantidad_normalizada, unidad_normalizada y conversión solo cuando sean razonables. "
                "Cada valor puede ser directo o un objeto con valor, confianza, motivo, fuente y url. "
                "Usa el contexto de menú y servicio cuando exista, sin presentarlo como dato documental. "
                "Si ni siquiera existe una estimación razonable, omite ese campo. "
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
            "provider": str(getattr(response, "proveedor", "") or ""),
            "model": str(getattr(response, "modelo", "") or ""),
        }
        logger.info("recipe_ai_proposal_filter %s", json.dumps(diagnostics, ensure_ascii=False, sort_keys=True))
        return GeneratedProposals(final, diagnostics)

    FIELD_LABELS = {key: str(spec["label"]) for key, spec in FIELD_CONTRACTS.items()}
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
    FIELDS = RECIPE_DOCUMENTATION_FIELDS
    _lock = RLock()

    def __init__(self, base_dir: Path, repository: RepositorioBibliotecaRecetas601 | None = None, generator: RecipeProposalGenerator | None = None) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.repository = repository or RepositorioBibliotecaRecetas601(base_dir)
        self.generator = generator or HostAIRecipeProposalGenerator(base_dir)
        self._completed: dict[str, dict[str, Any]] = {}

    def pending_field_keys(self, recipe: dict[str, Any]) -> list[str]:
        """Claves canónicas pendientes para contratos externos y providers."""
        return sorted(field for field in self.FIELDS if not self._field_complete(recipe, field))

    def normalize_proposed_value(self, field: str, value: Any) -> Any:
        """Autoridad tipada compartida por IA interna, XLSX y readiness."""
        if field not in self.FIELDS:
            raise RecetaDocumentacionError("unsupported_field", f"Campo no admitido: {field}.")
        if is_no_aplica(value):
            if field not in NO_APLICA_FIELDS:
                raise RecetaDocumentacionError("no_aplica_no_permitido", f"El campo {field} no admite NO_APLICA.")
            return deepcopy(NO_APLICA_VALUE)
        if isinstance(value, str) and self._normalized_text(value) in {
            "texto culinario provisional", "texto provisional", "por determinar", "sin dato",
        }:
            raise RecetaDocumentacionError("placeholder_value", "El valor es un comodín y no aporta información operativa.")
        if field in RECIPE_BOOLEAN_FIELDS:
            if isinstance(value, bool):
                return value
            normalized = str(value).strip().casefold()
            if normalized in {"true", "si", "sí", "yes", "1"}:
                return True
            if normalized in {"false", "no", "0"}:
                return False
            raise RecetaDocumentacionError("invalid_boolean", "Use true o false para este campo booleano.")
        if field in RECIPE_NUMBER_FIELDS:
            if isinstance(value, bool):
                raise RecetaDocumentacionError("invalid_number", "Use un número, no un booleano.")
            try:
                number = float(str(value).replace(",", "."))
            except (TypeError, ValueError):
                raise RecetaDocumentacionError("invalid_number", "Use un número válido.")
            if not math.isfinite(number):
                raise RecetaDocumentacionError("invalid_number", "Use un número finito válido.")
            if field == "merma":
                if number < 0 or number >= 1:
                    raise RecetaDocumentacionError("invalid_percentage", "La merma debe estar entre 0 y 1.")
            elif number <= 0:
                raise RecetaDocumentacionError("invalid_number", "El número debe ser mayor que cero.")
            return int(number) if number.is_integer() else number
        if field in RECIPE_TIME_FIELDS:
            text = str(value or "").strip()
            match = re.fullmatch(
                r"(\d+(?:[.,]\d+)?)\s*(?:h|horas?|min(?:uto)?s?|d[ií]as?|semanas?|mes(?:es)?)",
                self._normalized_text(text), flags=re.IGNORECASE,
            )
            if not match or not math.isfinite(float(match.group(1).replace(",", "."))) \
                    or float(match.group(1).replace(",", ".")) <= 0:
                raise RecetaDocumentacionError(
                    "invalid_duration", "Use una duración con número y unidad, por ejemplo '30 minutos'.",
                )
            return text
        if field in RECIPE_ENUM_FIELDS:
            normalized = self._normalized_text(value).replace(" ", "_").upper()
            if normalized not in RECIPE_ENUM_FIELDS[field]:
                allowed = ", ".join(RECIPE_ENUM_FIELDS[field])
                raise RecetaDocumentacionError("invalid_enum", f"Valor no admitido; use uno de: {allowed}.")
            return normalized
        if field in RECIPE_UNIT_FIELDS:
            normalized = self._normalized_unit(value)
            if normalized not in RECIPE_OPERATIONAL_UNITS:
                allowed = ", ".join(sorted(RECIPE_OPERATIONAL_UNITS))
                raise RecetaDocumentacionError("invalid_unit", f"Unidad no admitida; use una de: {allowed}.")
            return normalized
        if field in RECIPE_JSON_FIELDS:
            parsed = value
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                except ValueError:
                    raise RecetaDocumentacionError("invalid_structured_value", "Use JSON válido con el shape publicado.")
            if field == "ingredientes_estructurados":
                if not isinstance(parsed, list) or not parsed:
                    raise RecetaDocumentacionError("invalid_ingredient_proposal", "Los ingredientes deben ser una lista JSON no vacía.")
                return parsed
            if field == "cantidad_por_racion":
                if not isinstance(parsed, dict):
                    raise RecetaDocumentacionError("invalid_structured_shape", "Use {\"cantidad\": número, \"unidad\": unidad}.")
                quantity = self._positive_number(parsed.get("cantidad") or parsed.get("valor"))
                unit = self._normalized_unit(parsed.get("unidad"))
                if quantity is None or unit not in RECIPE_OPERATIONAL_UNITS:
                    raise RecetaDocumentacionError("invalid_structured_shape", "Cantidad por ración necesita cantidad positiva y unidad admitida.")
                return {"cantidad": quantity, "unidad": unit}
            if field == "personal_recomendado":
                if not isinstance(parsed, dict):
                    raise RecetaDocumentacionError("invalid_structured_shape", "Use {\"personas\": número, \"rol\": texto}.")
                people = self._positive_number(parsed.get("personas"))
                role = str(parsed.get("rol") or "").strip()
                if people is None or not role:
                    raise RecetaDocumentacionError("invalid_structured_shape", "Personal recomendado necesita personas y rol.")
                return {"personas": int(people) if people.is_integer() else people, "rol": role}
            if field == "recursos_necesarios":
                if not isinstance(parsed, list) or not parsed or any(not isinstance(item, str) or not item.strip() for item in parsed):
                    raise RecetaDocumentacionError("invalid_structured_shape", "Recursos necesarios debe ser una lista JSON de textos no vacíos.")
                return list(dict.fromkeys(item.strip() for item in parsed))
        if field == "alergenos":
            parsed = value
            if isinstance(value, str):
                text = value.strip()
                try:
                    parsed = json.loads(text)
                except ValueError:
                    raise RecetaDocumentacionError("invalid_allergen_list", "Use una lista JSON de alérgenos.")
            if not isinstance(parsed, (list, tuple)) or not parsed:
                raise RecetaDocumentacionError("empty_allergen_list", "Una lista vacía no afirma ausencia de alérgenos; deje la celda vacía.")
            if any(not isinstance(item, str) or not item.strip() for item in parsed):
                raise RecetaDocumentacionError("invalid_allergen_list", "Los alérgenos deben ser textos no vacíos.")
            allergens = list(dict.fromkeys(item.strip() for item in parsed))
            if any(self._normalized_text(item) in {"ninguno", "no aplica", "sin dato"} for item in allergens):
                raise RecetaDocumentacionError("invalid_allergen_list", "No use valores genéricos para afirmar ausencia de alérgenos.")
            return allergens
        if not isinstance(value, str):
            raise RecetaDocumentacionError("invalid_string", "Use texto para este campo.")
        text = value.strip()
        if not text:
            raise RecetaDocumentacionError("empty_value", "El valor está vacío.")
        return text

    def proposal_consistency_issues(
        self, current: dict[str, Any], proposals: dict[str, Any],
    ) -> dict[str, str]:
        """Contradicciones objetivas; nunca infiere política culinaria subjetiva."""
        effective = lambda field: proposals.get(field) if field in proposals else current.get(field)
        issues: dict[str, str] = {}

        def reject(preferred: str, fallback: str, code: str) -> None:
            field = preferred if self._present(effective(preferred)) else fallback
            if self._present(effective(field)):
                issues.setdefault(field, code)

        active = self._duration_minutes(effective("tiempo_activo"))
        total = self._duration_minutes(effective("tiempo_total"))
        passive_value = effective("tiempo_pasivo")
        passive = None if is_no_aplica(passive_value) else self._duration_minutes(passive_value)
        intervention = effective("intervencion_activa")
        if (intervention is False or is_no_aplica(intervention)) and active is not None and active > 0:
            reject("intervencion_activa", "tiempo_activo", "contradiction_active_intervention")
        if total is not None and active is not None and total < active:
            reject("tiempo_total", "tiempo_activo", "contradiction_total_below_active")
        if total is not None and passive is not None and total < passive:
            reject("tiempo_total", "tiempo_pasivo", "contradiction_total_below_passive")

        refrigerated = effective("puede_refrigerarse")
        refrigerated_life = effective("vida_util_refrigerado")
        if refrigerated is False and self._present(refrigerated_life) and not is_no_aplica(refrigerated_life):
            reject("vida_util_refrigerado", "puede_refrigerarse", "contradiction_refrigerated_life")
        if refrigerated is True and is_no_aplica(refrigerated_life):
            reject("vida_util_refrigerado", "puede_refrigerarse", "contradiction_refrigerated_no_aplica")

        frozen = effective("puede_congelarse")
        for dependent in ("vida_util_congelado", "tiempo_descongelacion"):
            dependent_value = effective(dependent)
            if frozen is False and self._present(dependent_value) and not is_no_aplica(dependent_value):
                reject(dependent, "puede_congelarse", f"contradiction_{dependent}")
            if frozen is True and is_no_aplica(dependent_value):
                reject(dependent, "puede_congelarse", f"contradiction_{dependent}_no_aplica")

        yield_value = self._positive_number(effective("rendimiento"))
        portions = self._positive_number(effective("numero_raciones"))
        yield_unit = self._normalized_unit(effective("unidad_rendimiento"))
        if yield_unit in {"raciones", "porciones"} and yield_value and portions and abs(yield_value - portions) > 1e-9:
            reject("rendimiento", "numero_raciones", "contradiction_yield_portions")
        portion_value = effective("cantidad_por_racion")
        if isinstance(portion_value, dict) and yield_value and portions:
            portion_quantity = self._positive_number(
                portion_value.get("cantidad") or portion_value.get("valor")
            )
            portion_unit = self._normalized_unit(portion_value.get("unidad"))
            normalized_portion, normalized_portion_unit = self._normalize_standard_quantity(
                portion_quantity or 0, portion_unit,
            )
            normalized_yield, normalized_yield_unit = self._normalize_standard_quantity(
                yield_value, yield_unit,
            )
            if (
                portion_quantity and normalized_portion_unit == normalized_yield_unit
                and normalized_portion_unit in {"kg", "l", "u"}
                and abs((normalized_portion * portions) - normalized_yield) > 1e-9
            ):
                reject("cantidad_por_racion", "rendimiento", "contradiction_portion_quantity_yield")
        batch_yield = self._positive_number(effective("rendimiento_por_tanda"))
        maximum = self._positive_number(effective("produccion_maxima"))
        if batch_yield and maximum and batch_yield > maximum:
            reject("rendimiento_por_tanda", "produccion_maxima", "contradiction_batch_above_maximum")
        return issues

    def proposal(self, *, recipe_id: str, proposed: dict[str, Any], detected_allergens: list[str] | None = None, session_id: str = "") -> dict[str, Any]:
        current = self._recipe(recipe_id)
        required_missing = list((current.get("completitud") or {}).get("campos_obligatorios_pendientes") or [])
        labels_by_key = HostAIRecipeProposalGenerator.FIELD_LABELS
        safe_missing = [
            labels_by_key[key] for key in sorted(self.FIELDS)
            if not self._field_complete(current, key) and key in labels_by_key
        ]
        missing = list(dict.fromkeys([*required_missing, *safe_missing]))
        non_proposable = [label for label in required_missing if HostAIRecipeProposalGenerator.MISSING_FIELD_KEYS.get(str(label).strip().casefold()) not in self.FIELDS]
        contextual_recipe = self._contextual_recipe(current)
        derived: dict[str, Any] = {}
        derived_metadata: dict[str, dict[str, Any]] = {}
        if not proposed:
            derived, derived_metadata = self._deterministic_proposals(current)
            remaining = [
                label for label in missing
                if HostAIRecipeProposalGenerator.MISSING_FIELD_KEYS.get(str(label).strip().casefold()) not in derived
            ]
            generated = (
                self.generator.generate(
                    recipe=contextual_recipe, missing_fields=remaining,
                    allowed_fields=set(self.FIELDS), session_id=session_id,
                )
                if isinstance(self.generator, HostAIRecipeProposalGenerator)
                else self.generator.generate(
                    recipe=contextual_recipe, missing_fields=remaining,
                    allowed_fields=set(self.FIELDS),
                )
            )
            proposed = {**dict(generated or {}), **derived}
            if isinstance(generated, GeneratedProposals):
                proposed = GeneratedProposals(proposed, dict(generated.diagnostics or {}))
        clean, metadata, normalization_discarded = self._normalize_proposals(
            current, dict(proposed or {}), derived_metadata=derived_metadata,
            diagnostics=dict(getattr(proposed, "diagnostics", {}) or {}),
        )
        clean = {key: value for key, value in clean.items() if key in self.FIELDS and self._present(value)}
        clean = {
            key: value for key, value in clean.items()
            if not self._field_complete(current, key)
        }
        diagnostics = dict(getattr(proposed, "diagnostics", {}) or {})
        discarded = [*list(diagnostics.get("discarded_keys") or []), *normalization_discarded]
        blocked_critical_content = []
        for key, value in list(clean.items()):
            findings = critical_free_text_findings(key, value)
            if not findings:
                continue
            clean.pop(key)
            metadata.pop(key, None)
            blocked_critical_content.append({
                "campo": key, "valor_propuesto": value, "motivos": findings,
                "accion": "CAMPO_RECHAZADO_PARA_REVISION",
            })
            discarded.append({"key": key, "reason": "CRITICAL_CONTENT_EMBEDDED"})
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
        return {
            "ok": True,
            "receta_id": str(current.get("id") or current.get("codigo")),
            "datos_existentes": {
                key: current.get(key) for key in self.FIELDS if self._present(current.get(key))
            },
            "datos_propuestos_ia": clean,
            "metadatos_propuestas": {key: metadata[key] for key in clean if key in metadata},
            "propuestas_bloqueadas_revision": blocked_critical_content,
            "campos_faltantes_motor": required_missing,
            "campos_pendientes_proponibles": safe_missing,
            "campos_pendientes_no_proponibles": non_proposable,
            "campos_descartados": discarded,
            "campos_sin_datos": sorted(key for key in self.FIELDS if not self._field_complete(current, key)),
            "alergenos_detectados_datos": list(detected_allergens or current.get("alergenos") or []),
            "alergenos_propuestos_ia": list(clean.get("alergenos") or []),
            "contexto_ia": deepcopy(contextual_recipe.get("_contexto_completado") or {}),
            "completitud": self._completion_projection(current, clean, metadata),
            "cost_breakdown": dict(diagnostics.get("cost_breakdown") or {}),
            "generado_ahora": True,
            "datos_reales_modificados": False,
        }

    def _contextual_recipe(self, current: dict[str, Any]) -> dict[str, Any]:
        recipe = deepcopy(current)
        context: dict[str, Any] = {
            "texto_original": current.get("texto_original") or current.get("notas_documentacion"),
            "procedencia_documental": deepcopy(current.get("procedencia_campos") or {}),
            "contexto_documental": {
                key: deepcopy(current.get(key)) for key in (
                    "origen", "import_id", "archivo_origen", "documento_origen",
                    "hoja_origen", "fila_origen", "celda_origen", "texto_original",
                    "notas_documentacion", "documentos_word", "documentos_pdf",
                    "documentos_fotografias",
                ) if self._present(current.get(key))
            },
            "menus": [], "contexto_servicio": [], "otros_usos": [],
            "articulos_relacionados": [], "ingredientes_contexto": [],
            "recetas_relacionadas": [],
            "campos_confirmados": {
                key: current.get(key) for key in sorted(self.FIELDS) if self._present(current.get(key))
            },
            "propuestas_previas": deepcopy(current.get("propuestas_ia_pendientes") or {}),
            "estados_campos_operativos": deepcopy(current.get("estados_campos_operativos") or {}),
        }
        provenance = dict(current.get("procedencia_campos") or {})
        context["datos_documentales"] = {
            key: deepcopy(current.get(key)) for key in sorted(self.FIELDS)
            if self._present(current.get(key))
            and str((provenance.get(key) or {}).get("tipo") or "DOCUMENTO").upper()
            in {"DOCUMENTO", "IMPORTADO", "REAL", "USUARIO", "CONFIRMADO"}
        }
        context["datos_calculados"] = {
            key: deepcopy(current.get(key)) for key in sorted(self.FIELDS)
            if self._present(current.get(key))
            and str((provenance.get(key) or {}).get("tipo") or "").upper() == "CALCULADO"
        }
        try:
            from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService

            response = BibliotecaCulinariaReadService(self.base_dir).detalle(
                str(current.get("id") or current.get("codigo") or "")
            )
            detail = dict(response.get("elaboracion") or {}) if response.get("ok") else {}
            context["menus"] = deepcopy(detail.get("menus") or [])
            context["contexto_servicio"] = [
                {
                    "menu_id": item.get("menu_id"), "menu": item.get("nombre"),
                    "tipo": item.get("tipo"), "servicio": item.get("servicio") or item.get("tipo"),
                    "pax": item.get("pax"), "estado": item.get("estado"),
                    "referencias_receta": deepcopy(item.get("referencias_receta") or []),
                }
                for item in context["menus"] if isinstance(item, dict)
            ]
            context["otros_usos"] = {
                "eventos": deepcopy(detail.get("eventos") or []),
                "menus": deepcopy(detail.get("menus") or []),
            }
            ingredients = list((detail.get("receta") or {}).get("ingredientes") or [])
            context["ingredientes_contexto"] = deepcopy(ingredients)
            context["articulos_relacionados"] = [
                {
                    "nombre_original": item.get("nombre_original"),
                    "article_id": item.get("articulo_id"),
                    "nombre": item.get("nombre_articulo"),
                    "cantidad_original": item.get("cantidad_texto"),
                    "unidad_original": item.get("unidad_original") or item.get("unidad"),
                    "cantidad_normalizada": item.get("cantidad_neta") or item.get("cantidad"),
                    "unidad_normalizada": item.get("unidad"),
                    "cantidad": item.get("cantidad"), "unidad": item.get("unidad"),
                    "merma": item.get("merma"),
                    "unidad_base": item.get("unidad_base"),
                    "unidad_compra": item.get("unidad_compra"),
                    "cantidad_formato": item.get("cantidad_formato"),
                    "unidad_formato": item.get("unidad_formato"),
                    "conversion_unidades": deepcopy(item.get("conversion_unidades") or []),
                    "coste_unitario": item.get("coste_unitario"),
                    "coste_linea": item.get("coste_linea"),
                    "precio": item.get("precio_original"),
                    "unidad_precio": item.get("unidad_precio_original"),
                    "precio_referencia": deepcopy(item.get("referencia_precio")),
                    "proveedor": deepcopy(item.get("proveedor") or item.get("proveedor_referencia")),
                    "tipo_precio": item.get("tipo_precio") or (
                        "REFERENCIA" if item.get("referencia_precio") else "CATALOGO"
                        if item.get("precio_original") not in (None, "") else "PENDIENTE"
                    ),
                    "estado_relacion": item.get("estado_relacion"),
                }
                for item in ingredients if isinstance(item, dict)
                and str(item.get("tipo_componente") or "ARTICULO").upper() == "ARTICULO"
            ]
            costing_lines = list((detail.get("escandallo") or {}).get("lineas") or [])
            article_index = 0
            for ingredient_position, ingredient in enumerate(ingredients):
                if not isinstance(ingredient, dict) or str(ingredient.get("tipo_componente") or "ARTICULO").upper() != "ARTICULO":
                    continue
                costing = costing_lines[ingredient_position] if ingredient_position < len(costing_lines) else {}
                related = context["articulos_relacionados"][article_index]
                related.update({
                    "precio": costing.get("precio_original") or costing.get("precio_aplicado") or related.get("precio"),
                    "unidad_precio": costing.get("unidad_precio_original") or costing.get("unidad_precio_aplicado") or related.get("unidad_precio"),
                    "precio_referencia": deepcopy(costing.get("referencia_precio") or related.get("precio_referencia")),
                    "proveedor": costing.get("proveedor_precio") or related.get("proveedor"),
                    "tipo_precio": costing.get("clasificacion_precio") or related.get("tipo_precio"),
                    "coste_unitario": costing.get("coste_unitario") or related.get("coste_unitario"),
                    "coste_linea": costing.get("coste_linea") or related.get("coste_linea"),
                })
                article_index += 1
            context["recetas_relacionadas"] = [
                {
                    "recipe_id": item.get("escandallo_hijo_id"),
                    "referencia": item.get("referencia_elaboracion"),
                    "nombre_original": item.get("nombre_original"),
                    "cantidad": item.get("cantidad"), "unidad": item.get("unidad"),
                    "estado_relacion": item.get("estado_relacion"),
                }
                for item in ingredients if isinstance(item, dict)
                and str(item.get("tipo_componente") or "").upper() == "ELABORACION"
            ]
        except Exception as exc:
            logger.warning("recipe_ai_context_unavailable recipe_id=%s error=%s", current.get("id"), exc)
        recipe["_contexto_completado"] = context
        return recipe

    def completion_context(self, recipe_id: str) -> dict[str, Any]:
        """Contexto culinario read-only compartido por IA y paquete externo."""
        current = self._recipe(recipe_id)
        contextual = self._contextual_recipe(current)
        return deepcopy(contextual.get("_contexto_completado") or {})

    def _deterministic_proposals(
        self, current: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
        values: dict[str, Any] = {}
        metadata: dict[str, dict[str, Any]] = {}

        def add(field: str, value: Any, reason: str) -> None:
            if field in self.FIELDS and not self._field_complete(current, field) and self._present(value):
                values[field] = value
                metadata[field] = proposal_metadata(
                    origin="CALCULADO", confidence=1.0, reason=reason, source="HOST_AI",
                )

        portions = self._positive_number(current.get("numero_raciones"))
        yield_value = self._positive_number(current.get("rendimiento"))
        yield_unit = str(current.get("unidad_rendimiento") or "").strip()
        if portions:
            add("rendimiento", portions, "Derivado del número de raciones ya informado.")
            add("unidad_rendimiento", "raciones", "La magnitud existente es número de raciones.")
        if yield_value and self._normalized_unit(yield_unit) == "raciones":
            add("numero_raciones", yield_value, "Derivado del rendimiento expresado en raciones.")
        active = self._duration_minutes(current.get("tiempo_activo"))
        passive = self._duration_minutes(current.get("tiempo_pasivo"))
        if active is not None and passive is not None:
            add("tiempo_total", f"{active + passive:g} minutos", "Suma determinista de tiempo activo y pasivo.")
        return values, metadata

    def _normalize_proposals(
        self, current: dict[str, Any], proposals: dict[str, Any], *,
        derived_metadata: dict[str, dict[str, Any]], diagnostics: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[dict[str, str]]]:
        clean: dict[str, Any] = {}
        metadata: dict[str, dict[str, Any]] = {}
        discarded: list[dict[str, str]] = []
        for field, raw in proposals.items():
            if field not in self.FIELDS:
                continue
            value = raw
            envelope: dict[str, Any] = {}
            if is_no_aplica(raw):
                if field not in NO_APLICA_FIELDS:
                    discarded.append({"key": field, "reason": "NO_APLICA_NO_PERMITIDO"})
                    continue
                value = deepcopy(NO_APLICA_VALUE)
                envelope = raw if isinstance(raw, dict) else {}
            if (
                not is_no_aplica(raw) and isinstance(raw, dict) and "valor" in raw
                and any(key in raw for key in {
                    "origen", "confianza", "motivo", "evidencia", "fuente", "url", "modelo",
                })
            ):
                value = raw.get("valor")
                envelope = raw
            try:
                value = self.normalize_proposed_value(field, value)
                if field == "ingredientes_estructurados":
                    value = self._normalize_ingredient_proposal(current, value)
            except RecetaDocumentacionError as exc:
                discarded.append({"key": field, "reason": exc.code})
                continue
            if not self._present(value):
                continue
            clean[field] = value
            if field in derived_metadata:
                metadata[field] = deepcopy(derived_metadata[field])
            else:
                confidence = envelope.get("confianza")
                try:
                    confidence = float(confidence) if confidence not in (None, "") else None
                except (TypeError, ValueError):
                    confidence = None
                metadata[field] = proposal_metadata(
                    origin=str(envelope.get("origen") or "IA_PROPUESTA"),
                    confidence=confidence,
                    reason=str(envelope.get("motivo") or envelope.get("evidencia") or "Propuesta del completador."),
                    source=str(envelope.get("fuente") or diagnostics.get("provider") or ""),
                    url=str(envelope.get("url") or ""),
                    model=str(envelope.get("modelo") or diagnostics.get("model") or ""),
                )
                if is_no_aplica(value):
                    metadata[field]["estado_campo"] = "NO_APLICA"
        for field, reason in self.proposal_consistency_issues(current, clean).items():
            if field not in clean:
                continue
            clean.pop(field, None)
            metadata.pop(field, None)
            discarded.append({"key": field, "reason": reason})
        return clean, metadata, discarded

    def _normalize_ingredient_proposal(
        self, current: dict[str, Any], value: Any,
    ) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            raise RecetaDocumentacionError("invalid_ingredient_proposal", "Los ingredientes propuestos deben ser una lista.")
        names = list(current.get("ingredientes") or [])
        existing = list(
            current.get("ingredientes_estructurados")
            or current.get("_ingredientes_estructurados") or []
        )
        if not names and existing:
            names = [
                str(item.get("nombre_original") or item.get("name_raw") or item.get("nombre") or "").strip()
                for item in existing if isinstance(item, dict)
            ]
        proposed_lines = []
        for proposed_line in value:
            if not isinstance(proposed_line, dict):
                raise RecetaDocumentacionError("invalid_ingredient_line", "Cada ingrediente propuesto debe ser estructurado.")
            proposed_lines.append(deepcopy(proposed_line))
        unused = set(range(len(proposed_lines)))
        output: list[dict[str, Any]] = []
        for index, original in enumerate(names):
            base = deepcopy(existing[index]) if index < len(existing) and isinstance(existing[index], dict) else {}
            original_name = str(original or "").strip()
            match = next((candidate_index for candidate_index in unused if self._normalized_text(
                proposed_lines[candidate_index].get("nombre_original")
                or proposed_lines[candidate_index].get("name_raw")
                or proposed_lines[candidate_index].get("nombre") or ""
            ) == self._normalized_text(original_name)), None)
            if match is None:
                raise RecetaDocumentacionError("ingredient_original_missing", "La propuesta no conserva todos los ingredientes originales.")
            proposed_line = proposed_lines[match]
            unused.remove(match)
            base_line_id = str(base.get("line_id") or "").strip()
            proposed_line_id = str(proposed_line.get("line_id") or "").strip()
            if base_line_id and proposed_line_id and proposed_line_id != base_line_id:
                raise RecetaDocumentacionError(
                    "ingredient_line_id_changed", "La identidad line_id de un ingrediente documental no se puede cambiar.",
                )
            base_article_id = str(base.get("articulo_id") or base.get("article_id") or "").strip()
            proposed_article_id = str(
                proposed_line.get("articulo_id") or proposed_line.get("article_id") or ""
            ).strip()
            if proposed_article_id and proposed_article_id != base_article_id:
                raise RecetaDocumentacionError(
                    "ingredient_article_link_unauthorized",
                    "Una propuesta externa no puede crear ni cambiar el enlace canónico a un artículo.",
                )
            line = {**base, **deepcopy(proposed_line)}
            if base_line_id:
                line["line_id"] = base_line_id
            if base_article_id:
                line["articulo_id"] = base_article_id
                line.pop("article_id", None)
            line["nombre_original"] = original_name
            line.setdefault("name_raw", original_name)
            current_article = str(base.get("article_id") or base.get("articulo_id") or "").strip()
            proposed_article = str(line.get("article_id") or line.get("articulo_id") or "").strip()
            if proposed_article and proposed_article != current_article:
                line.pop("article_id", None)
                line.pop("articulo_id", None)
            for protected in (
                "cantidad", "quantity", "cantidad_original", "cantidad_normalizada",
                "unidad", "unit", "unidad_normalizada", "merma", "merma_porcentaje",
            ):
                if self._present(base.get(protected)):
                    line[protected] = deepcopy(base[protected])
            quantity = self._positive_number(
                line.get("cantidad") or line.get("quantity") or line.get("cantidad_original")
            )
            normalized_quantity = self._positive_number(line.get("cantidad_normalizada"))
            unit = self._normalized_unit(line.get("unidad") or line.get("unit"))
            normalized_unit = self._normalized_unit(line.get("unidad_normalizada"))
            if unit and unit not in RECIPE_INGREDIENT_UNITS:
                raise RecetaDocumentacionError(
                    "invalid_ingredient_unit", "La unidad del ingrediente no está admitida para normalización y escandallo.",
                )
            if normalized_unit and normalized_unit not in {"kg", "l", "u"}:
                raise RecetaDocumentacionError(
                    "invalid_ingredient_unit", "La unidad normalizada del ingrediente debe ser kg, l o u.",
                )
            if quantity is not None:
                line["cantidad"] = quantity
            if unit:
                line["unidad"] = unit
            if normalized_quantity is None and quantity is not None and unit:
                normalized_quantity, normalized_unit = self._normalize_standard_quantity(quantity, unit)
            if normalized_quantity is not None:
                line["cantidad_normalizada"] = normalized_quantity
            if normalized_unit:
                line["unidad_normalizada"] = normalized_unit
            conversion = line.get("conversion")
            if conversion not in (None, ""):
                if not isinstance(conversion, dict) or self._positive_number(conversion.get("factor")) is None:
                    raise RecetaDocumentacionError("invalid_ingredient_conversion", "La conversión propuesta no es válida.")
                line["conversion"] = {
                    **conversion,
                    "factor": self._positive_number(conversion.get("factor")),
                    "origen": str(conversion.get("origen") or "IA_PROPUESTA"),
                    "estado_revision": "REQUIERE_REVISION_HUMANA",
                }
            line["dato_provisional"] = True
            line["procedencia_propuesta"] = deepcopy(
                proposed_line.get("procedencia_propuesta")
                if isinstance(proposed_line.get("procedencia_propuesta"), dict)
                else proposal_metadata(
                    origin="IA_PROPUESTA", confidence=self._confidence(proposed_line.get("confianza")),
                    reason=str(proposed_line.get("motivo") or "Unidad/cantidad propuesta por el completador."),
                )
            )
            output.append(line)
        for candidate_index in sorted(unused):
            proposed_line = proposed_lines[candidate_index]
            proposed_name = str(
                proposed_line.get("nombre_original") or proposed_line.get("name_raw")
                or proposed_line.get("nombre") or ""
            ).strip()
            if not proposed_name:
                raise RecetaDocumentacionError("invalid_ingredient_line", "Cada ingrediente candidato necesita nombre_original.")
            if proposed_line.get("articulo_id") or proposed_line.get("article_id"):
                raise RecetaDocumentacionError(
                    "ingredient_article_link_unauthorized",
                    "Un candidato nuevo no puede atribuirse un artículo canónico sin alta autorizada.",
                )
            normalized_name = self._normalized_text(proposed_name)
            existing_names = {
                self._normalized_text(item.get("nombre_original") or item.get("name_raw") or item.get("nombre") or "")
                for item in output if isinstance(item, dict)
            }
            if normalized_name in existing_names:
                raise RecetaDocumentacionError(
                    "duplicate_ingredient_candidate", "Un ingrediente no puede repetirse como candidato ni duplicar una línea documental.",
                )
            line = deepcopy(proposed_line)
            line["nombre_original"] = proposed_name
            line.setdefault("name_raw", proposed_name)
            line.pop("article_id", None)
            line.pop("articulo_id", None)
            quantity = self._positive_number(
                line.get("cantidad") or line.get("quantity") or line.get("cantidad_original")
            )
            unit = self._normalized_unit(line.get("unidad") or line.get("unit"))
            if quantity is None or unit not in RECIPE_INGREDIENT_UNITS:
                raise RecetaDocumentacionError(
                    "invalid_new_ingredient_candidate",
                    "Un ingrediente nuevo necesita cantidad positiva y una unidad admitida para quedar como candidato provisional.",
                )
            line["cantidad"] = quantity
            line["unidad"] = unit
            normalized_quantity = self._positive_number(line.get("cantidad_normalizada"))
            normalized_unit = self._normalized_unit(line.get("unidad_normalizada"))
            if normalized_unit and normalized_unit not in {"kg", "l", "u"}:
                raise RecetaDocumentacionError(
                    "invalid_ingredient_unit", "La unidad normalizada del ingrediente debe ser kg, l o u.",
                )
            if normalized_quantity is None or not normalized_unit:
                normalized_quantity, normalized_unit = self._normalize_standard_quantity(quantity, unit)
            line["cantidad_normalizada"] = normalized_quantity
            line["unidad_normalizada"] = normalized_unit
            line["estado_relacion"] = "CANDIDATO_NUEVO"
            line["dato_provisional"] = True
            line["procedencia_propuesta"] = deepcopy(
                proposed_line.get("procedencia_propuesta")
                if isinstance(proposed_line.get("procedencia_propuesta"), dict)
                else proposal_metadata(
                    origin="IA_PROPUESTA", confidence=self._confidence(proposed_line.get("confianza")),
                    reason=str(proposed_line.get("motivo") or "Ingrediente nuevo propuesto como candidato; requiere alta autorizada."),
                )
            )
            output.append(line)
        line_ids = [str(item.get("line_id") or "").strip() for item in output]
        populated_line_ids = [value for value in line_ids if value]
        if len(populated_line_ids) != len(set(populated_line_ids)):
            raise RecetaDocumentacionError(
                "duplicate_ingredient_line_id", "Cada line_id de ingrediente debe ser único.",
            )
        return output

    def _completion_projection(
        self, current: dict[str, Any], proposals: dict[str, Any], metadata: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        tracked = sorted(self.FIELDS)
        total = len(tracked)
        origins = dict(current.get("procedencia_campos") or {})
        confirmed = sum(self._field_complete(current, field) for field in tracked)
        documental = sum(
            self._field_complete(current, field)
            and str((origins.get(field) or {}).get("tipo") or "DOCUMENTO").upper()
            in {"DOCUMENTO", "IMPORTADO", "REAL", "CONFIRMADO", "USUARIO"}
            for field in tracked
        )
        with_proposals = sum(
            self._field_complete(current, field)
            or self._proposal_completes_field(current, field, proposals.get(field))
            for field in tracked
        )
        percent = lambda count: round((count / total) * 100, 2) if total else 0.0
        field_states: dict[str, str] = {}
        persisted_states = dict(current.get("estados_campos_operativos") or {})
        for field in tracked:
            persisted_state = str((persisted_states.get(field) or {}).get("estado") or "").upper()
            if persisted_state == "NO_APLICA":
                field_states[field] = "NO_APLICA"
            elif self._field_complete(current, field):
                field_states[field] = "CONFIRMADO"
            elif field in proposals:
                field_states[field] = "NO_APLICA" if is_no_aplica(proposals[field]) else "PROPUESTO"
            else:
                field_states[field] = "PENDIENTE"
        readiness = self._production_readiness(current, proposals, metadata)
        return {
            "documental": {"porcentaje": percent(documental), "campos": documental, "total": total},
            "propuesta": {"porcentaje": percent(with_proposals), "campos": with_proposals, "total": total},
            "confirmada": {"porcentaje": percent(confirmed), "campos": confirmed, "total": total},
            "pendientes": [
                field for field in tracked
                if not self._field_complete(current, field)
                and not self._proposal_completes_field(current, field, proposals.get(field))
            ],
            "origenes_propuestos": {key: value.get("origen") for key, value in metadata.items()},
            "estados_campos": field_states,
            "no_aplica": sorted(field for field, state in field_states.items() if state == "NO_APLICA"),
            **readiness,
        }

    def _production_readiness(
        self, current: dict[str, Any], proposals: dict[str, Any],
        metadata: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Calcula suficiencia de planificación sobre datos actuales o una proyección read-only."""
        required = set(PRODUCTION_READINESS_BASE_FIELDS)

        def effective(field: str) -> Any:
            return proposals.get(field) if field in proposals else current.get(field)

        for controlling_field, conditions in PRODUCTION_READINESS_CONDITIONAL_FIELDS.items():
            required.update(conditions.get(effective(controlling_field), ()))

        confirmed_blockers = {
            field for field in required if not self._field_complete(current, field)
        }
        provisional_blockers = {
            field for field in required
            if not self._field_complete(current, field)
            and not self._proposal_completes_field(current, field, proposals.get(field))
        }
        confirmed_blockers.update(self.proposal_consistency_issues(current, {}))
        provisional_blockers.update(self.proposal_consistency_issues(current, proposals))
        confirmed_blockers = sorted(confirmed_blockers)
        provisional_blockers = sorted(provisional_blockers)
        current_origins = dict(current.get("procedencia_campos") or {})
        origin_states = {
            "DOCUMENTO": "RESUELTO_DOCUMENTO", "IMPORTADO": "RESUELTO_DOCUMENTO",
            "REAL": "RESUELTO_DOCUMENTO", "USUARIO": "RESUELTO_DOCUMENTO",
            "CONFIRMADO": "CONFIRMADO", "CALCULADO": "RESUELTO_CALCULO",
            "CONTEXTO_INTERNO": "RESUELTO_CONTEXTO", "IA_PROPUESTA": "RESUELTO_IA",
            "REFERENCIA_EXTERNA": "RESUELTO_REFERENCIA",
        }
        resolution: dict[str, dict[str, Any]] = {}
        for field in sorted(self.FIELDS):
            current_state = str(((current.get("estados_campos_operativos") or {}).get(field) or {}).get("estado") or "").upper()
            if current_state == "NO_APLICA" or is_no_aplica(proposals.get(field)):
                status, origin = "NO_APLICA", "NO_APLICA"
            elif self._field_complete(current, field):
                origin = str((current_origins.get(field) or {}).get("tipo") or "DOCUMENTO").upper()
                status = origin_states.get(origin, "RESUELTO_DOCUMENTO")
            elif self._proposal_completes_field(current, field, proposals.get(field)):
                origin = str((metadata.get(field) or {}).get("origen") or "IA_PROPUESTA").upper()
                status = origin_states.get(origin, "RESUELTO_IA")
            else:
                status, origin = "PENDIENTE", ""
            resolution[field] = {
                "estado": status, "origen": origin or None,
                "motivo": (metadata.get(field) or {}).get("motivo") or None,
            }
        return {
            "production_ready_provisional": not provisional_blockers,
            "production_ready_confirmed": not confirmed_blockers,
            "production_ready": {
                "provisional": not provisional_blockers,
                "confirmed": not confirmed_blockers,
                "campos_requeridos": sorted(required),
                "bloqueos_provisionales": provisional_blockers,
                "bloqueos_confirmados": confirmed_blockers,
            },
            "resolucion_campos": resolution,
        }

    @staticmethod
    def _positive_number(value: Any) -> float | None:
        if isinstance(value, bool) or value in (None, ""):
            return None
        try:
            number = float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            return None
        return number if math.isfinite(number) and number > 0 else None

    @staticmethod
    def _confidence(value: Any) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return min(1.0, max(0.0, number)) if math.isfinite(number) else None

    @staticmethod
    def _duration_minutes(value: Any) -> float | None:
        text = str(value or "").strip().casefold().replace(",", ".")
        match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(h|hora|horas|min|minuto|minutos)", text)
        if not match:
            return None
        number = float(match.group(1))
        if not math.isfinite(number) or number <= 0:
            return None
        return number * 60 if str(match.group(2)).startswith("h") else number

    @staticmethod
    def _normalized_text(value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or "").strip().casefold())
        return " ".join("".join(char for char in text if not unicodedata.combining(char)).split())

    @classmethod
    def _normalized_unit(cls, value: Any) -> str:
        unit = cls._normalized_text(value)
        aliases = {
            "kilogramo": "kg", "kilogramos": "kg", "gramo": "g", "gramos": "g",
            "litro": "l", "litros": "l", "mililitro": "ml", "mililitros": "ml",
            "centilitro": "cl", "centilitros": "cl", "ud": "u", "uds": "u",
            "unidad": "u", "unidades": "u", "racion": "raciones", "raciones": "raciones",
        }
        return aliases.get(unit, unit)

    @classmethod
    def _normalize_standard_quantity(cls, quantity: float, unit: str) -> tuple[float, str]:
        normalized = cls._normalized_unit(unit)
        factors = {"g": (0.001, "kg"), "kg": (1.0, "kg"), "ml": (0.001, "l"), "cl": (0.01, "l"), "l": (1.0, "l"), "u": (1.0, "u")}
        factor, target = factors.get(normalized, (1.0, normalized))
        return round(quantity * factor, 9), target

    def preview(
        self, *, recipe_id: str, selected: dict[str, Any], overwrite_fields: list[str],
        context: AuthorizedExecutionContext, proposal_source: dict[str, Any] | None = None,
        proposal_metadata_by_field: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self._authorize(context)
        current = self._recipe(recipe_id)
        changes = self._validate_selection(current, selected, overwrite_fields)
        source = self._proposal_source(proposal_source)
        metadata = {
            key: deepcopy(value) for key, value in dict(proposal_metadata_by_field or {}).items()
            if key in changes and isinstance(value, dict)
        }
        for key in changes:
            metadata.setdefault(key, proposal_metadata(
                origin="IA_PROPUESTA" if source["origen_externo"] != "HUMANO" else "CONFIRMADO",
                reason="Propuesta seleccionada para revisión humana.",
                source=source["fuente"],
            ))
        token = self._token(current, changes, context, source, metadata)
        proposed_recipe = deepcopy(current)
        projected_states = deepcopy(dict(current.get("estados_campos_operativos") or {}))
        for field, value in changes.items():
            if is_no_aplica(value):
                projected_states[field] = {
                    "estado": "NO_APLICA", "confirmado": False,
                    "estado_revision": "REQUIERE_REVISION_HUMANA",
                }
            else:
                proposed_recipe[field] = value
        if projected_states:
            proposed_recipe["estados_campos_operativos"] = projected_states
        return {
            "ok": True, "estado": "LISTO_PARA_CONFIRMAR" if changes else "SIN_CAMBIOS",
            "receta_antes": current, "cambios_seleccionados": changes,
            "receta_propuesta": proposed_recipe, "preview_token": token,
            "requiere_confirmacion": bool(changes), "procedencia_propuesta": source,
            "metadatos_propuestas": metadata, "datos_reales_modificados": False,
        }

    def confirm(
        self, *, recipe_id: str, selected: dict[str, Any], overwrite_fields: list[str],
        preview_token: str, context: AuthorizedExecutionContext,
        proposal_source: dict[str, Any] | None = None,
        proposal_metadata_by_field: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            if preview_token in self._completed:
                return {**self._completed[preview_token], "idempotente": True}
            source = self._proposal_source(proposal_source)
            preview = self.preview(
                recipe_id=recipe_id, selected=selected, overwrite_fields=overwrite_fields,
                context=context, proposal_source=source,
                proposal_metadata_by_field=proposal_metadata_by_field,
            )
            if not preview_token or preview_token != preview["preview_token"]: raise RecetaDocumentacionError("stale_or_invalid_preview", "La vista previa ya no es válida.")
            if not preview["requiere_confirmacion"]: return {**preview, "idempotente": True}
            current = preview["receta_antes"]
            now = datetime.now().isoformat(timespec="seconds")
            origins = dict(current.get("procedencia_campos") or {})
            history = list(current.get("historial_procedencia") or [])
            persisted_changes = {
                field: self._confirmed_value(field, value, now=now, actor=context.user_id)
                for field, value in preview["cambios_seleccionados"].items()
                if not is_no_aplica(value)
            }
            operational_states = deepcopy(dict(current.get("estados_campos_operativos") or {}))
            for field, value in preview["cambios_seleccionados"].items():
                metadata = deepcopy((preview.get("metadatos_propuestas") or {}).get(field) or {})
                proposal_origin = str(metadata.get("origen") or "IA_PROPUESTA")
                origin_type = "USUARIO" if source["origen_externo"] == "HUMANO" else "IA"
                history.append({
                    "campo": field, "valor_anterior": current.get(field), "valor_nuevo": value,
                    "origen_anterior": origins.get(field), "origen_nuevo": origin_type,
                    "actor": context.user_id, "timestamp": now,
                    "estado_revision": "CONFIRMADO", "fuente_propuesta": source["fuente"],
                    "origen_propuesta": proposal_origin,
                    "origen_externo": source["origen_externo"], "metadatos_propuesta": metadata,
                })
                origins[field] = {
                    **metadata, "tipo": origin_type, "actor_id": context.user_id,
                    "fecha": now, "estado_revision": "CONFIRMADO", "confirmado": True,
                    "origen_propuesta": proposal_origin,
                    "fuente_propuesta": source["fuente"], "origen_externo": source["origen_externo"],
                }
                if is_no_aplica(value):
                    operational_states[field] = {
                        **metadata, "estado": "NO_APLICA", "confirmado": True,
                        "confirmado_en": now, "confirmado_por": context.user_id,
                        "estado_revision": "CONFIRMADO",
                    }
                else:
                    operational_states.pop(field, None)
            changes_to_store = {
                **persisted_changes, "procedencia_campos": origins,
                "historial_procedencia": history,
            }
            if operational_states:
                changes_to_store["estados_campos_operativos"] = operational_states
            incomplete_editor = getattr(self.repository, "editar_borrador_incompleto", None)
            if (
                str(current.get("estado") or "").upper() == "PENDIENTE_DE_COMPLETAR"
                and callable(incomplete_editor)
            ):
                result = incomplete_editor(recipe_id, changes_to_store)
            else:
                result = self.repository.editar(recipe_id, changes_to_store)
            if not result.get("ok"): raise RecetaDocumentacionError("write_failed", " | ".join(result.get("errores") or ["No se pudo guardar."]))
            persisted = self._recipe(recipe_id)
            states_verified = all(
                str(((persisted.get("estados_campos_operativos") or {}).get(field) or {}).get("estado") or "").upper()
                == "NO_APLICA"
                for field, value in preview["cambios_seleccionados"].items() if is_no_aplica(value)
            )
            response = {"ok": True, "estado": "CONFIRMADO", "receta": persisted, "campos_confirmados": sorted(preview["cambios_seleccionados"]), "idempotente": False, "datos_reales_modificados": True, "lectura_posterior_verificada": states_verified and all(self._equivalent(persisted.get(key), value) for key, value in persisted_changes.items())}
            self._completed[preview_token] = response
            return response

    def _validate_selection(self, current: dict[str, Any], selected: dict[str, Any], overwrite_fields: list[str]) -> dict[str, Any]:
        overwrites = set(overwrite_fields or [])
        changes = {}
        for key, value in dict(selected or {}).items():
            if key not in self.FIELDS: raise RecetaDocumentacionError("unsupported_field", f"Campo no admitido: {key}.")
            if is_no_aplica(value) and key not in NO_APLICA_FIELDS:
                raise RecetaDocumentacionError("no_aplica_no_permitido", f"El campo {key} no admite NO_APLICA.")
            if not self._present(value): continue
            existing_state = str(((current.get("estados_campos_operativos") or {}).get(key) or {}).get("estado") or "").upper()
            if is_no_aplica(value) and existing_state == "NO_APLICA":
                continue
            enrichment = key == "ingredientes_estructurados" and self._ingredient_enrichment_only(
                current, value,
            )
            if self._field_complete(current, key) and current.get(key) != value and key not in overwrites and not enrichment:
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

    def _field_complete(self, recipe: dict[str, Any], field: str) -> bool:
        state = str(((recipe.get("estados_campos_operativos") or {}).get(field) or {}).get("estado") or "").upper()
        if field in NO_APLICA_FIELDS and state == "NO_APLICA":
            return True
        if field == "ingredientes_estructurados":
            lines = list(
                recipe.get("ingredientes_estructurados")
                or recipe.get("_ingredientes_estructurados") or []
            )
            names = list(recipe.get("ingredientes") or [])
            return bool(lines) and len(lines) >= len(names) and all(
                isinstance(line, dict)
                and self._positive_number(
                    line.get("cantidad") or line.get("quantity") or line.get("cantidad_original")
                ) is not None
                and self._normalized_unit(line.get("unidad") or line.get("unit")) in RECIPE_INGREDIENT_UNITS
                for line in lines
            )
        value = (
            recipe.get("categoria") or recipe.get("familia") or recipe.get("tipo")
            if field == "categoria" else recipe.get(field)
        )
        if not self._present(value):
            return False
        try:
            self.normalize_proposed_value(field, value)
            return True
        except RecetaDocumentacionError:
            return False

    def _proposal_completes_field(
        self, current: dict[str, Any], field: str, value: Any,
    ) -> bool:
        if is_no_aplica(value):
            return field in NO_APLICA_FIELDS
        if not self._present(value):
            return False
        if field != "ingredientes_estructurados":
            try:
                self.normalize_proposed_value(field, value)
                return True
            except RecetaDocumentacionError:
                return False
        if not isinstance(value, list):
            return False
        projected = {**current, "ingredientes_estructurados": value}
        return self._field_complete(projected, field)

    def _ingredient_enrichment_only(self, current: dict[str, Any], proposed: Any) -> bool:
        if not isinstance(proposed, list):
            return False
        existing = list(
            current.get("ingredientes_estructurados")
            or current.get("_ingredientes_estructurados") or []
        )
        if not existing or len(existing) != len(proposed):
            return False
        protected = (
            "nombre_original", "name_raw", "nombre", "article_id", "articulo_id",
            "cantidad", "quantity", "cantidad_original", "cantidad_normalizada",
            "unidad", "unit", "unidad_normalizada", "merma", "merma_porcentaje",
        )
        for before, after in zip(existing, proposed):
            if not isinstance(before, dict) or not isinstance(after, dict):
                return False
            for key in protected:
                if self._present(before.get(key)) and after.get(key) != before.get(key):
                    return False
        return True

    @staticmethod
    def _equivalent(persisted: Any, proposed: Any) -> bool:
        if persisted == proposed:
            return True
        if isinstance(persisted, bool) or isinstance(proposed, bool):
            return False
        try:
            return float(str(persisted).replace(",", ".")) == float(str(proposed).replace(",", "."))
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _confirmed_value(field: str, value: Any, *, now: str, actor: str) -> Any:
        if field != "ingredientes_estructurados" or not isinstance(value, list):
            return deepcopy(value)
        confirmed = []
        for raw in value:
            line = deepcopy(raw)
            if isinstance(line, dict):
                line.pop("dato_provisional", None)
                provenance = dict(line.get("procedencia_propuesta") or {})
                line["procedencia_propuesta"] = {
                    **provenance, "estado_revision": "CONFIRMADO", "confirmado": True,
                    "confirmado_en": now, "confirmado_por": actor,
                }
                conversion = line.get("conversion")
                if isinstance(conversion, dict):
                    line["conversion"] = {
                        **conversion, "estado_revision": "CONFIRMADO", "confirmado": True,
                    }
            confirmed.append(line)
        return confirmed

    @staticmethod
    def _proposal_source(source: dict[str, Any] | None) -> dict[str, str]:
        value = dict(source or {})
        external = str(value.get("origen_externo") or "OPENAI_API").strip().upper()
        if external not in {"CHATGPT", "OPENAI_API", "OTRO_PROVEEDOR_IA", "HUMANO", "ARCHIVO_EXTERNO"}:
            external = "ARCHIVO_EXTERNO"
        channel = str(value.get("fuente") or "HOST_AI_API").strip().upper()
        if channel not in {"HOST_AI_API", "ARCHIVO_EXTERNO"}:
            channel = "ARCHIVO_EXTERNO"
        return {"fuente": channel, "origen_externo": external}

    @staticmethod
    def _token(
        current: dict[str, Any], changes: dict[str, Any], context: AuthorizedExecutionContext,
        source: dict[str, str], metadata: dict[str, dict[str, Any]] | None = None,
    ) -> str:
        stable_metadata = {
            key: {name: value for name, value in dict(item or {}).items() if name != "fecha"}
            for key, item in dict(metadata or {}).items()
        }
        raw = json.dumps({
            "current": current, "changes": changes, "actor": context.user_id,
            "tenant": context.tenant_id, "source": source, "metadata": stable_metadata,
        }, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()


__all__ = [
    "RecetaDocumentacionWriteService", "RecetaDocumentacionError",
    "RecipeProposalGenerator", "HostAIRecipeProposalGenerator",
    "BATCH_MASS_SAFE_FIELDS", "BATCH_INDIVIDUAL_REVIEW_FIELDS",
    "classify_recipe_proposals", "classify_recipe_proposals_for_review",
    "critical_free_text_findings",
    "recipe_completion_fingerprint",
    "NO_APLICA_FIELDS", "NO_APLICA_VALUE", "is_no_aplica",
    "RECIPE_BOOLEAN_FIELDS", "RECIPE_NUMBER_FIELDS", "RECIPE_TIME_FIELDS",
    "RECIPE_JSON_FIELDS", "RECIPE_ENUM_FIELDS", "RECIPE_UNIT_FIELDS",
    "RECIPE_OPERATIONAL_UNITS", "RECIPE_INGREDIENT_UNITS",
]
