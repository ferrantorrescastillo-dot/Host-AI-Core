from __future__ import annotations

import hashlib
import inspect
import json
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.motor_escritura_segura_i1342 import MotorEscrituraSeguraI1342
from SERVICIOS.receta_documentacion_write_service import (
    BATCH_GROUP_REVIEW_FIELDS,
    BATCH_MASS_SAFE_FIELDS,
    RecetaDocumentacionError,
    RecetaDocumentacionWriteService,
    classify_recipe_proposals_for_review,
    recipe_completion_fingerprint,
)

BATCH_STORE_PATH = "DATOS/db/biblioteca_completado_recetas_batches.json"
BATCH_STORE_SCHEMA_VERSION = 3


class RecipeCompletionBatchRepository:
    """Persistencia del workflow; no contiene ni modifica recetas canónicas."""

    def __init__(self, base_dir: Path, *, persistent: bool = True) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.path = self.base_dir / BATCH_STORE_PATH
        self.persistent = persistent
        self.created_at = ""

    def load(self) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
        if not self.persistent:
            return {}, {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}, {}
        self.created_at = str(payload.get("created_at") or "") if isinstance(payload, dict) else ""
        batches = payload.get("batches") if isinstance(payload, dict) else {}
        confirms = payload.get("completed_confirms") if isinstance(payload, dict) else {}
        return (
            deepcopy(batches) if isinstance(batches, dict) else {},
            deepcopy(confirms) if isinstance(confirms, dict) else {},
        )

    def save(
        self,
        batches: dict[str, dict[str, Any]],
        completed_confirms: dict[str, dict[str, Any]],
    ) -> None:
        if not self.persistent:
            return
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if not self.created_at:
            self.created_at = now
        motor = MotorEscrituraSeguraI1342(self.base_dir, [BATCH_STORE_PATH])
        result = motor.ejecutar({
            BATCH_STORE_PATH: {
                "version": 1,
                "schema_version": BATCH_STORE_SCHEMA_VERSION,
                "created_at": self.created_at,
                "updated_at": now,
                "batches": batches,
                "completed_confirms": completed_confirms,
            },
        })
        if result.estado != "COMMIT":
            raise RuntimeError(result.error or "No se pudo persistir el workflow de completado de recetas.")


class RecetaDocumentacionBatchService:
    """Orquesta el flujo individual para N recetas sin conceder WRITE a la IA."""

    _lock = RLock()
    MAX_PROVIDER_ATTEMPTS = 3

    def __init__(
        self,
        base_dir: Path,
        *,
        recipe_service: RecetaDocumentacionWriteService | None = None,
        repository: RepositorioBibliotecaRecetas601 | None = None,
        state_repository: RecipeCompletionBatchRepository | None = None,
        persistent_state: bool = True,
    ) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.repository = repository or RepositorioBibliotecaRecetas601(base_dir)
        self.recipe_service = recipe_service or RecetaDocumentacionWriteService(base_dir, repository=self.repository)
        self.state_repository = state_repository or RecipeCompletionBatchRepository(
            base_dir, persistent=persistent_state,
        )
        self.read_service = BibliotecaCulinariaReadService(base_dir)
        self._batches, self._completed_confirms = self.state_repository.load()
        for batch in self._batches.values():
            batch["schema_version"] = BATCH_STORE_SCHEMA_VERSION
            batch.setdefault("selecciones_agrupadas", {})
            batch.setdefault("referencias_precio_externas", [])
            batch.setdefault("archivo_externo", None)
            for item in (batch.get("resultados") or {}).values():
                proposals = dict(item.get("datos_propuestos_ia") or {})
                safe, grouped, individual = classify_recipe_proposals_for_review(
                    proposals
                )
                item["datos_propuestos_seguros_masivo"] = safe
                item["datos_operativos_agrupables"] = grouped
                item["datos_requieren_revision_individual"] = individual
                if proposals and batch["referencias_precio_externas"]:
                    refreshed = self._provisional_projection(
                        str(item.get("recipe_id") or ""), proposals,
                        dict(item.get("metadatos_propuestas") or {}),
                        dict(item.get("completitud") or {}),
                        price_references=batch["referencias_precio_externas"],
                    )
                    if refreshed is not None:
                        item["proyeccion_provisional"] = refreshed
            self._refresh_preview_projection(batch)
        for batch in self._batches.values():
            # Un proceso interrumpido se reanuda desde la cola persistida.
            batch["procesando"] = ""
            batch["confirmando"] = False

    def summary(self) -> dict[str, Any]:
        recipes = self.repository.listar()
        incomplete = [item for item in recipes if self._missing(item)]
        return {"ok": True, "recetas_incompletas": len(incomplete), "recipe_ids": [self._id(item) for item in incomplete]}

    def start(self, *, recipe_ids: list[str] | None = None) -> dict[str, Any]:
        recipes = self.repository.listar()
        by_id = {self._id(item): item for item in recipes if self._id(item)}
        if recipe_ids is None:
            queue = [self._id(item) for item in recipes if self._missing(item)]
        else:
            requested = list(dict.fromkeys(
                str(item).strip() for item in recipe_ids if str(item).strip()
            ))
            # Una seleccion explicita define toda la frontera del batch. Incluimos
            # las ya completas para informar YA_COMPLETA, pero nunca incorporamos
            # recetas ajenas ni convertimos [] en "toda la Biblioteca".
            queue = [recipe_id for recipe_id in requested if recipe_id in by_id]
        batch = self._create_batch(queue)
        self._finish_generation(batch)
        self._persist()
        return self._public(batch)

    def start_external(
        self,
        *,
        proposal_results: list[dict[str, Any]],
        validation: dict[str, Any],
        price_references: list[dict[str, Any]] | None = None,
        file_receipt: dict[str, Any] | None = None,
        import_id: str = "",
        scope: str = "BIBLIOTECA",
    ) -> dict[str, Any]:
        validation_rows = list(validation.get("filas") or [])
        queue = list(dict.fromkeys([
            str(item.get("recipe_id") or "")
            for item in validation_rows
            if str(item.get("recipe_id") or "")
        ] or [str(item.get("recipe_id") or "") for item in proposal_results]))
        batch = self._create_batch(queue)
        batch["modo_generacion"] = "ARCHIVO_EXTERNO"
        batch["import_id"] = str(import_id or validation.get("import_id") or "")
        batch["scope"] = str(scope or validation.get("scope") or "BIBLIOTECA")
        batch["validacion_externa"] = dict(validation or {})
        batch["referencias_precio_externas"] = deepcopy(price_references or [])
        batch["archivo_externo"] = deepcopy(file_receipt) if file_receipt else None
        for item in proposal_results:
            recipe_id = str(item.get("recipe_id") or "")
            current = self.repository.obtener(recipe_id)
            result = dict(item.get("proposal_result") or {})
            if not current:
                continue
            batch["fuentes_propuesta"][recipe_id] = dict(item.get("proposal_source") or {})
            batch["fingerprints_externos"][recipe_id] = str(item.get("recipe_fingerprint") or "")
            self._store_proposal_result(batch, recipe_id, current, result, attempts=0)
            validation_row = next((
                row for row in validation_rows
                if str(row.get("recipe_id") or "") == recipe_id
            ), None)
            if validation_row:
                batch["resultados"][recipe_id]["validacion_fila"] = deepcopy(validation_row)
        for row in validation_rows:
            recipe_id = str(row.get("recipe_id") or "")
            if not recipe_id or recipe_id in batch["resultados"]:
                continue
            validation_failed = bool(row.get("errores")) or row.get("estado") == "RECHAZADA"
            validation_only_result = {
                "recipe_id": recipe_id,
                "nombre": (self.repository.obtener(recipe_id) or {}).get("nombre", recipe_id),
                "estado": "ERROR_VALIDACION" if validation_failed else "NECESITA_USUARIO",
                "datos_propuestos_ia": {}, "datos_propuestos_seguros_masivo": {},
                "datos_operativos_agrupables": {},
                "datos_requieren_revision_individual": {},
                "propuestas_bloqueadas_revision": deepcopy(row.get("campos_bloqueados") or []),
                "campos_pendientes_no_proponibles": [],
                "validacion_fila": deepcopy(row),
                "completitud": {"production_ready_provisional": False, "production_ready_confirmed": False},
            }
            if validation_failed:
                validation_only_result["error"] = {
                    "code": "external_row_rejected",
                    "message": " | ".join(row.get("errores") or ["Fila externa rechazada."]),
                }
            batch["resultados"][recipe_id] = validation_only_result
        self._finish_generation(batch)
        self._persist()
        return self._public(batch)

    def active_external(self, import_id: str) -> dict[str, Any]:
        identity = str(import_id or "").strip()
        candidates = [
            batch for batch in self._batches.values()
            if batch.get("modo_generacion") == "ARCHIVO_EXTERNO"
            and str(batch.get("import_id") or "") == identity
            and batch.get("estado") != "CANCELADO"
        ]
        batch = candidates[-1] if candidates else None
        return {
            "ok": True,
            "importacion_id": identity,
            "batch": self._public(batch) if batch else None,
            "datos_reales_modificados": False,
        }

    def get(self, batch_id: str) -> dict[str, Any]:
        return self._public(self._batch(batch_id))

    def next(self, batch_id: str, *, session_id: str = "") -> dict[str, Any]:
        batch = self._batch(batch_id)
        with self._lock:
            if batch["cancelado"]:
                return self._public(batch)
            pending = [item for item in batch["recipe_ids"] if item not in batch["resultados"]]
            if not pending:
                self._finish_generation(batch)
                self._persist()
                return self._public(batch)
            recipe_id = pending[0]
            current = self.repository.obtener(recipe_id)
            if not current or not self._missing(current):
                batch["resultados"][recipe_id] = {"recipe_id": recipe_id, "nombre": (current or {}).get("nombre", recipe_id), "estado": "YA_COMPLETA", "datos_propuestos_ia": {}, "campos_pendientes_no_proponibles": []}
            else:
                batch["procesando"] = recipe_id
                attempts = int(batch["intentos_provider"].get(recipe_id, 0)) + 1
                batch["intentos_provider"][recipe_id] = attempts
                try:
                    result = self.recipe_service.proposal(recipe_id=recipe_id, proposed={}, session_id=session_id)
                except RecetaDocumentacionError as exc:
                    if not self._provider_error(exc):
                        batch["procesando"] = ""
                        raise
                    batch["resultados"][recipe_id] = {
                        "recipe_id": recipe_id,
                        "nombre": current.get("nombre", recipe_id),
                        "estado": "ERROR_PROVIDER",
                        "datos_propuestos_ia": {},
                        "datos_propuestos_seguros_masivo": {},
                        "datos_requieren_revision_individual": {},
                        "propuestas_bloqueadas_revision": [],
                        "campos_pendientes_no_proponibles": [],
                        "error": {"code": exc.code, "message": str(exc)},
                        "categoria_error": exc.code.removeprefix("ai_provider_").removeprefix("ai_"),
                        "intentos": attempts,
                        "fallo_en": self._now(),
                        "reintento_disponible": attempts < self.MAX_PROVIDER_ATTEMPTS,
                        "backoff_recomendado_segundos": min(2 ** (attempts - 1), 8),
                    }
                    batch["procesando"] = ""
                    self._finish_generation(batch)
                    self._persist()
                    return self._public(batch)
                batch["procesando"] = ""
                batch["fuentes_propuesta"][recipe_id] = {
                    "fuente": "HOST_AI_API", "origen_externo": "OPENAI_API",
                }
                self._store_proposal_result(batch, recipe_id, current, result, attempts=attempts)
            self._finish_generation(batch)
            self._persist()
            return self._public(batch)

    def cancel(self, batch_id: str) -> dict[str, Any]:
        batch = self._batch(batch_id)
        batch["cancelado"] = True
        batch["estado"] = "CANCELADO"
        self._persist()
        return self._public(batch)

    def retry(self, batch_id: str, recipe_id: str) -> dict[str, Any]:
        batch = self._batch(batch_id)
        if batch["cancelado"]:
            raise RecetaDocumentacionError("batch_cancelled", "El proceso masivo esta cancelado.")
        recipe_id = str(recipe_id)
        result = batch["resultados"].get(recipe_id)
        if not result or result.get("estado") != "ERROR_PROVIDER":
            raise RecetaDocumentacionError("recipe_not_retryable", "La receta no tiene un fallo de proveedor reintentable.")
        if int(batch["intentos_provider"].get(recipe_id, 0)) >= self.MAX_PROVIDER_ATTEMPTS:
            raise RecetaDocumentacionError("provider_retry_limit", "La receta alcanzo el limite de reintentos del proveedor.")
        batch["resultados"].pop(recipe_id, None)
        batch["estado"] = "GENERANDO"
        batch["preview"] = None
        self._persist()
        return self._public(batch)

    def retry_failed(self, batch_id: str) -> dict[str, Any]:
        batch = self._batch(batch_id)
        if batch["cancelado"]:
            raise RecetaDocumentacionError("batch_cancelled", "El proceso masivo esta cancelado.")
        retryable = [
            recipe_id for recipe_id, result in batch["resultados"].items()
            if result.get("estado") == "ERROR_PROVIDER"
            and int(batch["intentos_provider"].get(recipe_id, 0)) < self.MAX_PROVIDER_ATTEMPTS
        ]
        for recipe_id in retryable:
            batch["resultados"].pop(recipe_id, None)
        if retryable:
            batch["estado"] = "GENERANDO"
            batch["preview"] = None
            self._persist()
        return self._public(batch)

    def select(
        self,
        batch_id: str,
        selections: dict[str, dict[str, Any]],
        individual_selections: dict[str, dict[str, Any]] | None = None,
        grouped_selections: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        batch = self._batch(batch_id)
        clean: dict[str, dict[str, Any]] = {}
        for recipe_id, fields in dict(selections or {}).items():
            proposed = dict((batch["resultados"].get(recipe_id) or {}).get("datos_propuestos_seguros_masivo") or {})
            clean[recipe_id] = {key: value for key, value in dict(fields or {}).items() if key in proposed and value == proposed[key]}
        batch["selecciones"] = clean
        if individual_selections is not None:
            reviewed: dict[str, dict[str, Any]] = {}
            for recipe_id, fields in dict(individual_selections or {}).items():
                proposed = dict((batch["resultados"].get(recipe_id) or {}).get("datos_requieren_revision_individual") or {})
                reviewed[recipe_id] = {
                    key: value for key, value in dict(fields or {}).items()
                    if key in proposed and value == proposed[key]
                }
            batch["selecciones_individuales"] = reviewed
        if grouped_selections is not None:
            grouped: dict[str, dict[str, Any]] = {}
            for recipe_id, fields in dict(grouped_selections or {}).items():
                proposed = dict((batch["resultados"].get(recipe_id) or {}).get("datos_operativos_agrupables") or {})
                grouped[recipe_id] = {
                    key: value for key, value in dict(fields or {}).items()
                    if key in proposed and value == proposed[key]
                }
            batch["selecciones_agrupadas"] = grouped
        batch["preview"] = None
        self._persist()
        return self._public(batch)

    def preview(self, batch_id: str, *, context: AuthorizedExecutionContext) -> dict[str, Any]:
        batch = self._batch(batch_id)
        items = []
        recipe_ids = list(dict.fromkeys([
            *batch["selecciones"].keys(), *batch["selecciones_agrupadas"].keys(),
            *batch["selecciones_individuales"].keys(),
        ]))
        for recipe_id in recipe_ids:
            current = self.repository.obtener(recipe_id)
            expected_fingerprint = str(batch["fingerprints_externos"].get(recipe_id) or "")
            if expected_fingerprint:
                if not current or recipe_completion_fingerprint(current) != expected_fingerprint:
                    raise RecetaDocumentacionError("stale_external_recipe", f"La receta {recipe_id} cambio desde la exportacion externa.")
            selected = {
                **dict(batch["selecciones"].get(recipe_id) or {}),
                **dict(batch["selecciones_agrupadas"].get(recipe_id) or {}),
                **dict(batch["selecciones_individuales"].get(recipe_id) or {}),
            }
            if not selected:
                continue
            source = dict(batch["fuentes_propuesta"].get(recipe_id) or {})
            result_record = dict(batch["resultados"].get(recipe_id) or {})
            proposal_metadata_by_field = {
                key: deepcopy(value)
                for key, value in dict(result_record.get("metadatos_propuestas") or {}).items()
                if key in selected and isinstance(value, dict)
            }
            preview_kwargs = {
                "recipe_id": recipe_id, "selected": selected, "overwrite_fields": [],
                "context": context, "proposal_source": source,
                "proposal_metadata_by_field": proposal_metadata_by_field,
            }
            item = self.recipe_service.preview(**self._supported_kwargs(
                self.recipe_service.preview, preview_kwargs,
            ))
            changes = dict(item["cambios_seleccionados"])
            current = dict(item.get("receta_antes") or current or {})
            source = dict(item.get("procedencia_propuesta") or source)
            individual_fields = set((batch["selecciones_individuales"].get(recipe_id) or {}).keys())
            grouped_fields = set((batch["selecciones_agrupadas"].get(recipe_id) or {}).keys())
            change_details = []
            for field, proposed_value in changes.items():
                current_value = current.get(field)
                current_present = current_value is not None and current_value != "" and current_value != []
                field_metadata = deepcopy(proposal_metadata_by_field.get(field) or {})
                change_details.append({
                    "campo": field,
                    "valor_actual": current_value,
                    "valor_propuesto": proposed_value,
                    "procedencia": {**source, **field_metadata},
                    "clasificacion": (
                        "REVISION_INDIVIDUAL" if field in individual_fields
                        else "REVISION_AGRUPADA" if field in grouped_fields
                        else "SELECCION_MASIVA"
                    ),
                    "sobrescribe": bool(current_present and current_value != proposed_value),
                    "completa": not current_present,
                })
            items.append({
                "recipe_id": recipe_id,
                "nombre": (batch["resultados"].get(recipe_id) or {}).get("nombre"),
                "cambios": changes,
                "detalle_cambios": change_details,
                "preview_token": item["preview_token"],
                "proposal_source": source,
                "metadatos_propuestas": proposal_metadata_by_field,
                # La ficha y el escandallo describen la proyección provisional
                # completa de la receta. El detalle de cambios sigue limitado a
                # la selección autorizada y es la única entrada de confirm().
                "proyeccion_provisional": deepcopy(
                    result_record.get("proyeccion_provisional")
                ),
            })
        fingerprint = hashlib.sha256(json.dumps(items, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        batch["preview"] = {"fingerprint": fingerprint, "recetas_afectadas": len(items), "cambios_a_aplicar": sum(len(item["cambios"]) for item in items), "items": items}
        batch["estado"] = "PREVIEW"
        self._persist()
        return self._public(batch)

    def confirm(self, batch_id: str, *, fingerprint: str, context: AuthorizedExecutionContext) -> dict[str, Any]:
        batch = self._batch(batch_id)
        preview = batch.get("preview") or {}
        if not fingerprint or fingerprint != preview.get("fingerprint"):
            raise RecetaDocumentacionError("stale_or_invalid_preview", "La vista previa masiva ya no es valida.")
        if fingerprint in self._completed_confirms:
            return {**self._completed_confirms[fingerprint], "idempotente": True}
        with self._lock:
            if batch["confirmando"]:
                raise RecetaDocumentacionError("confirm_in_flight", "La confirmacion ya esta en curso.")
            batch["confirmando"] = True
            applied, failed = [], []
            try:
                for item in preview.get("items", []):
                    try:
                        confirm_kwargs = {
                            "recipe_id": item["recipe_id"], "selected": item["cambios"],
                            "overwrite_fields": [], "preview_token": item["preview_token"],
                            "context": context,
                            "proposal_source": dict(item.get("proposal_source") or {}),
                            "proposal_metadata_by_field": dict(item.get("metadatos_propuestas") or {}),
                        }
                        result = self.recipe_service.confirm(**self._supported_kwargs(
                            self.recipe_service.confirm, confirm_kwargs,
                        ))
                        applied.append({"recipe_id": item["recipe_id"], "campos": result.get("campos_confirmados", []), "lectura_posterior_verificada": result.get("lectura_posterior_verificada", False)})
                    except Exception as exc:
                        failed.append({"recipe_id": item["recipe_id"], "error": str(exc)})
            finally:
                batch["confirmando"] = False
            response = {"ok": not failed, "estado": "COMPLETADO" if not failed else "COMPLETADO_PARCIAL", "aplicadas": applied, "fallidas": failed, "recetas_incompletas": self.summary()["recetas_incompletas"], "idempotente": False}
            self._completed_confirms[fingerprint] = response
            batch["estado"] = response["estado"]
            batch["resultado_confirmacion"] = response
            self._persist()
            return response

    def _public(self, batch: dict[str, Any]) -> dict[str, Any]:
        results = []
        for raw in batch["resultados"].values():
            item = deepcopy(raw)
            coverage = dict(item.get("completitud") or {})
            individual = set((item.get("datos_requieren_revision_individual") or {}).keys())
            selected_individual = set((batch.get("selecciones_individuales", {}).get(item.get("recipe_id")) or {}).keys())
            grouped = set((item.get("datos_operativos_agrupables") or {}).keys())
            selected_grouped = set((batch.get("selecciones_agrupadas", {}).get(item.get("recipe_id")) or {}).keys())
            low_confidence_fields = []
            for field, value in (item.get("metadatos_propuestas") or {}).items():
                if not isinstance(value, dict) or value.get("confianza") in (None, ""):
                    continue
                try:
                    if float(value["confianza"]) < 0.5:
                        low_confidence_fields.append(field)
                except (TypeError, ValueError):
                    low_confidence_fields.append(field)
            costing = dict((item.get("proyeccion_provisional") or {}).get("escandallo") or {})
            resolution = dict(coverage.get("resolucion_campos") or {})
            exceptions = {
                "bloqueada": not bool(coverage.get("production_ready_provisional")),
                "no_production_ready": not bool(coverage.get("production_ready_provisional")),
                "criticos": bool(individual - selected_individual),
                "baja_confianza": bool(low_confidence_fields),
                "operativas_agrupables": bool(grouped - selected_grouped),
                "pendientes": bool(coverage.get("pendientes")),
                "no_aplica": bool(coverage.get("no_aplica")),
                "error": bool(
                    str(item.get("estado") or "").startswith("ERROR")
                    or (item.get("validacion_fila") or {}).get("errores")
                ),
                "precios_proveedores": bool(
                    (costing.get("ingredientes_sin_coste") or 0)
                    or (costing.get("ingredientes_sin_conversion") or 0)
                ),
                "imposible_estimar": any(
                    str(value.get("estado") or "") == "IMPOSIBLE_ESTIMAR_RAZONABLEMENTE"
                    for value in resolution.values() if isinstance(value, dict)
                ),
            }
            item["excepciones"] = exceptions
            item["campos_baja_confianza_relevante"] = sorted(low_confidence_fields)
            item["estado_operativo"] = (
                "PRODUCTION_READY_PROVISIONAL"
                if coverage.get("production_ready_provisional") else item.get("estado")
            )
            results.append(item)
        result_by_id = batch["resultados"]
        total = len(batch["recipe_ids"])
        failed = sum(str(item.get("estado") or "").startswith("ERROR") for item in results)
        provider_failed = sum(item.get("estado") == "ERROR_PROVIDER" for item in results)
        successful = sum(
            item.get("estado") in {"CON_PROPUESTAS", "NECESITA_USUARIO", "YA_COMPLETA"}
            for item in results
        )
        processing = str(batch.get("procesando") or "")
        queue = [{
            "recipe_id": recipe_id,
            "estado": "PROCESANDO" if recipe_id == processing else (result_by_id.get(recipe_id) or {}).get("estado", "PENDIENTE"),
        } for recipe_id in batch["recipe_ids"]]
        cost_items = [dict(item.get("cost_breakdown") or {}) for item in results]
        usage_items = [entry for cost in cost_items for entry in list(cost.get("items") or []) if isinstance(entry, dict)]
        estimated_cost = sum(
            float(item.get("total_cost_usd") or item.get("estimated_cost_usd") or item.get("cost_usd") or 0)
            for item in cost_items
        )
        external_validation = dict(batch.get("validacion_externa") or {})
        validation_error_rows = sum(
            bool(row.get("errores")) for row in external_validation.get("filas") or []
            if isinstance(row, dict)
        )
        mass_summary = {
            "recetas_procesadas": int(external_validation.get("filas_recibidas") or total),
            "production_ready_provisional": sum(
                bool((item.get("completitud") or {}).get("production_ready_provisional")) for item in results
            ),
            "production_ready_confirmed": sum(
                bool((item.get("completitud") or {}).get("production_ready_confirmed")) for item in results
            ),
            "criticos_pendientes": sum(bool(item["excepciones"]["criticos"]) for item in results),
            "campos_criticos_individuales": sum(
                len(item.get("datos_requieren_revision_individual") or {}) for item in results
            ),
            "campos_operativos_agrupables": sum(
                len(item.get("datos_operativos_agrupables") or {}) for item in results
            ),
            "recetas_sin_excepciones_operativas_relevantes": sum(
                not any(item["excepciones"].get(key) for key in (
                    "bloqueada", "baja_confianza", "error", "imposible_estimar",
                )) for item in results
            ),
            "articulos_precios_pendientes": sum(bool(item["excepciones"]["precios_proveedores"]) for item in results),
            "baja_confianza": sum(bool(item["excepciones"]["baja_confianza"]) for item in results),
            "errores": provider_failed + validation_error_rows,
            "imposibles_estimar": sum(bool(item["excepciones"]["imposible_estimar"]) for item in results),
            "no_aplica": sum(bool(item["excepciones"]["no_aplica"]) for item in results),
            "escandallos_provisionales": sum(
                ((item.get("proyeccion_provisional") or {}).get("escandallo") or {}).get("estado_coste") == "PROVISIONAL"
                for item in results
            ),
            "escandallos_parciales": sum(
                ((item.get("proyeccion_provisional") or {}).get("escandallo") or {}).get("estado_coste") == "PARCIAL"
                for item in results
            ),
            "escandallos_sin_coste": sum(
                ((item.get("proyeccion_provisional") or {}).get("escandallo") or {}).get("estado_coste") == "SIN_COSTE"
                for item in results
            ),
            "datos_reales_modificados": False,
        }
        return {
            "ok": True, **batch, "resultados": results, "cola": queue,
            "resumen_masivo": mass_summary,
            "metricas_ia": {
                "recetas": total,
                "llamadas": sum(int(value) for value in batch["intentos_provider"].values()),
                "reintentos": sum(max(0, int(value) - 1) for value in batch["intentos_provider"].values()),
                "errores_provider": provider_failed,
                "tokens": sum(int(item.get("total_tokens") or 0) for item in usage_items),
                "providers": sorted({str(item.get("provider")) for item in usage_items if item.get("provider")}),
                "modelos": sorted({str(item.get("model")) for item in usage_items if item.get("model")}),
                "coste_estimado_usd": estimated_cost,
                "coste_disponible": any(
                    "total_cost_usd" in item or "estimated_cost_usd" in item or "cost_usd" in item
                    for item in cost_items
                ),
            },
            "progreso": {
                "total": total, "analizadas": len(results), "exitosas": successful,
                "fallidas": failed, "pendientes": max(0, total - len(results) - (1 if processing else 0)),
                "con_propuestas": sum(item.get("estado") == "CON_PROPUESTAS" for item in results),
                "necesitan_usuario": sum(item.get("estado") == "NECESITA_USUARIO" for item in results),
                "ya_completas": sum(item.get("estado") == "YA_COMPLETA" for item in results),
                "propuestas": sum(len(item.get("datos_propuestos_ia") or {}) for item in results),
            },
        }

    @staticmethod
    def _provider_error(exc: RecetaDocumentacionError) -> bool:
        return exc.code.startswith("ai_provider_") or exc.code == "ai_invalid_response"

    @staticmethod
    def _supported_kwargs(callable_object: Any, values: dict[str, Any]) -> dict[str, Any]:
        """Mantiene compatibles adaptadores inyectados anteriores al metadato por campo."""
        parameters = inspect.signature(callable_object).parameters.values()
        if any(parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in parameters):
            return values
        accepted = {parameter.name for parameter in parameters}
        return {key: value for key, value in values.items() if key in accepted}

    @staticmethod
    def _finish_generation(batch: dict[str, Any]) -> None:
        if batch["cancelado"]:
            return
        if len(batch["resultados"]) < len(batch["recipe_ids"]):
            batch["estado"] = "GENERANDO"
            return
        has_errors = any(
            str(item.get("estado") or "").startswith("ERROR")
            for item in batch["resultados"].values()
        )
        has_errors = has_errors or any(
            bool(row.get("errores"))
            for row in (batch.get("validacion_externa") or {}).get("filas") or []
            if isinstance(row, dict)
        )
        batch["estado"] = "PROPUESTAS_LISTAS_CON_ERRORES" if has_errors else "PROPUESTAS_LISTAS"

    def _create_batch(self, queue: list[str]) -> dict[str, Any]:
        batch_id = "RECIPE-BATCH-" + uuid.uuid4().hex[:12].upper()
        batch = {
            "batch_id": batch_id, "estado": "GENERANDO", "recipe_ids": list(queue),
            "schema_version": BATCH_STORE_SCHEMA_VERSION,
            "resultados": {}, "selecciones": {}, "selecciones_agrupadas": {},
            "selecciones_individuales": {},
            "intentos_provider": {}, "fuentes_propuesta": {}, "fingerprints_externos": {}, "preview": None,
            "procesando": "", "modo_generacion": "HOST_AI_API",
            "archivo_externo": None,
            "referencias_precio_externas": [],
            "cancelado": False, "confirmando": False, "creado_en": self._now(),
            "created_at": self._now(), "updated_at": self._now(),
        }
        self._batches[batch_id] = batch
        return batch

    def _store_proposal_result(
        self,
        batch: dict[str, Any],
        recipe_id: str,
        current: dict[str, Any],
        result: dict[str, Any],
        *,
        attempts: int,
    ) -> None:
        proposals = dict(result.get("datos_propuestos_ia") or {})
        proposal_metadata_by_field = dict(result.get("metadatos_propuestas") or {})
        safe_mass, grouped_review, individual_review = classify_recipe_proposals_for_review(proposals)
        result["datos_propuestos_ia"] = proposals
        batch["resultados"][recipe_id] = {
            **result, "recipe_id": recipe_id, "nombre": current.get("nombre", recipe_id),
            "estado": "CON_PROPUESTAS" if proposals else "NECESITA_USUARIO",
            "datos_propuestos_seguros_masivo": safe_mass,
            "datos_operativos_agrupables": grouped_review,
            "datos_requieren_revision_individual": individual_review,
            "intentos": attempts,
            "proyeccion_provisional": self._provisional_projection(
                recipe_id, proposals, proposal_metadata_by_field, result.get("completitud"),
                price_references=batch.get("referencias_precio_externas") or [],
            ),
            "propuestas_estructuradas": [{
                "recipe_id": recipe_id, "campo": field, "valor_actual": current.get(field),
                "valor_propuesto": value, "origen": "IA_PROPUESTA", "estado": "PROPUESTA",
                "timestamp": self._now(),
                "procedencia": deepcopy(proposal_metadata_by_field.get(field) or {}),
            } for field, value in proposals.items()],
        }

    def _provisional_projection(
        self, recipe_id: str, proposals: dict[str, Any],
        metadata: dict[str, dict[str, Any]], completeness: dict[str, Any] | None,
        *, price_references: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        try:
            response = self.read_service.proyectar_provisional(
                recipe_id, propuestas=proposals,
                metadatos_propuestas=metadata, completitud=dict(completeness or {}),
                campos_revision_individual=sorted(set(proposals) - BATCH_MASS_SAFE_FIELDS - BATCH_GROUP_REVIEW_FIELDS),
                referencias_precio=deepcopy(price_references or []),
            )
            return response if response.get("ok") else None
        except Exception:
            return None

    @staticmethod
    def _refresh_preview_projection(batch: dict[str, Any]) -> None:
        """Rehidrata derivados del preview sin ampliar los cambios confirmables."""
        preview = batch.get("preview")
        if not isinstance(preview, dict):
            return
        items = preview.get("items")
        if not isinstance(items, list):
            return
        results = dict(batch.get("resultados") or {})
        for item in items:
            if not isinstance(item, dict):
                continue
            result = dict(results.get(str(item.get("recipe_id") or "")) or {})
            item["proyeccion_provisional"] = deepcopy(
                result.get("proyeccion_provisional")
            )
        preview["fingerprint"] = hashlib.sha256(
            json.dumps(items, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()

    def _batch(self, batch_id: str) -> dict[str, Any]:
        batch = self._batches.get(str(batch_id))
        if not batch:
            raise RecetaDocumentacionError("batch_not_found", "Proceso masivo no encontrado.")
        return batch

    def _persist(self) -> None:
        now = self._now()
        for batch in self._batches.values():
            if int(batch.get("schema_version") or 0) >= BATCH_STORE_SCHEMA_VERSION:
                batch["updated_at"] = now
        self.state_repository.save(self._batches, self._completed_confirms)

    @staticmethod
    def _missing(recipe: dict[str, Any]) -> list[str]:
        return list((recipe.get("completitud") or {}).get("campos_obligatorios_pendientes") or [])

    @staticmethod
    def _id(recipe: dict[str, Any]) -> str:
        return str(recipe.get("id") or recipe.get("codigo") or "")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")


__all__ = [
    "BATCH_STORE_PATH", "BATCH_STORE_SCHEMA_VERSION", "RecipeCompletionBatchRepository",
    "RecetaDocumentacionBatchService",
]
