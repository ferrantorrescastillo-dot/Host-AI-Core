from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any

from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.receta_documentacion_write_service import (
    RecetaDocumentacionError,
    RecetaDocumentacionWriteService,
)


class RecetaDocumentacionBatchService:
    """Orquesta el flujo individual para N recetas sin conceder WRITE a la IA."""

    _lock = RLock()

    def __init__(
        self,
        base_dir: Path,
        *,
        recipe_service: RecetaDocumentacionWriteService | None = None,
        repository: RepositorioBibliotecaRecetas601 | None = None,
    ) -> None:
        self.repository = repository or RepositorioBibliotecaRecetas601(base_dir)
        self.recipe_service = recipe_service or RecetaDocumentacionWriteService(base_dir, repository=self.repository)
        self._batches: dict[str, dict[str, Any]] = {}
        self._completed_confirms: dict[str, dict[str, Any]] = {}

    def summary(self) -> dict[str, Any]:
        recipes = self.repository.listar()
        incomplete = [item for item in recipes if self._missing(item)]
        return {"ok": True, "recetas_incompletas": len(incomplete), "recipe_ids": [self._id(item) for item in incomplete]}

    def start(self, *, recipe_ids: list[str] | None = None) -> dict[str, Any]:
        requested = {str(item) for item in (recipe_ids or []) if str(item).strip()}
        recipes = [item for item in self.repository.listar() if not requested or self._id(item) in requested]
        queue = [self._id(item) for item in recipes if self._missing(item)]
        batch_id = "RECIPE-BATCH-" + uuid.uuid4().hex[:12].upper()
        batch = {
            "batch_id": batch_id, "estado": "GENERANDO", "recipe_ids": queue,
            "resultados": {}, "selecciones": {}, "preview": None,
            "cancelado": False, "confirmando": False, "creado_en": self._now(),
        }
        self._batches[batch_id] = batch
        return self._public(batch)

    def get(self, batch_id: str) -> dict[str, Any]:
        return self._public(self._batch(batch_id))

    def next(self, batch_id: str, *, session_id: str = "") -> dict[str, Any]:
        batch = self._batch(batch_id)
        with self._lock:
            if batch["cancelado"]:
                return self._public(batch)
            pending = [item for item in batch["recipe_ids"] if item not in batch["resultados"]]
            if not pending:
                batch["estado"] = "PROPUESTAS_LISTAS"
                return self._public(batch)
            recipe_id = pending[0]
            current = self.repository.obtener(recipe_id)
            if not current or not self._missing(current):
                batch["resultados"][recipe_id] = {"recipe_id": recipe_id, "nombre": (current or {}).get("nombre", recipe_id), "estado": "YA_COMPLETA", "datos_propuestos_ia": {}, "campos_pendientes_no_proponibles": []}
            else:
                result = self.recipe_service.proposal(recipe_id=recipe_id, proposed={}, session_id=session_id)
                proposals = dict(result.get("datos_propuestos_ia") or {})
                # El rendimiento es un dato culinario real: en masa nunca se acepta una
                # cifra inferida sin revisión humana individual.
                if "numero_raciones" in proposals:
                    proposals.pop("numero_raciones")
                    result["campos_pendientes_no_proponibles"] = list(dict.fromkeys([
                        *list(result.get("campos_pendientes_no_proponibles") or []), "Rendimiento",
                    ]))
                result["datos_propuestos_ia"] = proposals
                batch["resultados"][recipe_id] = {
                    **result, "recipe_id": recipe_id, "nombre": current.get("nombre", recipe_id),
                    "estado": "CON_PROPUESTAS" if proposals else "NECESITA_USUARIO",
                    "propuestas_estructuradas": [{
                        "recipe_id": recipe_id, "campo": field, "valor_actual": current.get(field),
                        "valor_propuesto": value, "origen": "IA", "estado": "PROPUESTA",
                        "timestamp": self._now(),
                    } for field, value in proposals.items()],
                }
            if len(batch["resultados"]) == len(batch["recipe_ids"]):
                batch["estado"] = "PROPUESTAS_LISTAS"
            return self._public(batch)

    def cancel(self, batch_id: str) -> dict[str, Any]:
        batch = self._batch(batch_id)
        batch["cancelado"] = True
        batch["estado"] = "CANCELADO"
        return self._public(batch)

    def select(self, batch_id: str, selections: dict[str, dict[str, Any]]) -> dict[str, Any]:
        batch = self._batch(batch_id)
        clean: dict[str, dict[str, Any]] = {}
        for recipe_id, fields in dict(selections or {}).items():
            proposed = dict((batch["resultados"].get(recipe_id) or {}).get("datos_propuestos_ia") or {})
            clean[recipe_id] = {key: value for key, value in dict(fields or {}).items() if key in proposed and value == proposed[key]}
        batch["selecciones"] = clean
        batch["preview"] = None
        return self._public(batch)

    def preview(self, batch_id: str, *, context: AuthorizedExecutionContext) -> dict[str, Any]:
        batch = self._batch(batch_id)
        items = []
        for recipe_id, selected in batch["selecciones"].items():
            if not selected:
                continue
            item = self.recipe_service.preview(recipe_id=recipe_id, selected=selected, overwrite_fields=[], context=context)
            items.append({"recipe_id": recipe_id, "nombre": (batch["resultados"].get(recipe_id) or {}).get("nombre"), "cambios": item["cambios_seleccionados"], "preview_token": item["preview_token"]})
        fingerprint = hashlib.sha256(json.dumps(items, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        batch["preview"] = {"fingerprint": fingerprint, "recetas_afectadas": len(items), "cambios_a_aplicar": sum(len(item["cambios"]) for item in items), "items": items}
        batch["estado"] = "PREVIEW"
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
                        result = self.recipe_service.confirm(recipe_id=item["recipe_id"], selected=item["cambios"], overwrite_fields=[], preview_token=item["preview_token"], context=context)
                        applied.append({"recipe_id": item["recipe_id"], "campos": result.get("campos_confirmados", []), "lectura_posterior_verificada": result.get("lectura_posterior_verificada", False)})
                    except Exception as exc:
                        failed.append({"recipe_id": item["recipe_id"], "error": str(exc)})
            finally:
                batch["confirmando"] = False
            response = {"ok": not failed, "estado": "COMPLETADO" if not failed else "COMPLETADO_PARCIAL", "aplicadas": applied, "fallidas": failed, "recetas_incompletas": self.summary()["recetas_incompletas"], "idempotente": False}
            self._completed_confirms[fingerprint] = response
            batch["estado"] = response["estado"]
            batch["resultado_confirmacion"] = response
            return response

    def _public(self, batch: dict[str, Any]) -> dict[str, Any]:
        results = list(batch["resultados"].values())
        return {**batch, "resultados": results, "progreso": {"total": len(batch["recipe_ids"]), "analizadas": len(results), "con_propuestas": sum(item.get("estado") == "CON_PROPUESTAS" for item in results), "necesitan_usuario": sum(item.get("estado") == "NECESITA_USUARIO" for item in results), "ya_completas": sum(item.get("estado") == "YA_COMPLETA" for item in results), "propuestas": sum(len(item.get("datos_propuestos_ia") or {}) for item in results)}}

    def _batch(self, batch_id: str) -> dict[str, Any]:
        batch = self._batches.get(str(batch_id))
        if not batch:
            raise RecetaDocumentacionError("batch_not_found", "Proceso masivo no encontrado.")
        return batch

    @staticmethod
    def _missing(recipe: dict[str, Any]) -> list[str]:
        return list((recipe.get("completitud") or {}).get("campos_obligatorios_pendientes") or [])

    @staticmethod
    def _id(recipe: dict[str, Any]) -> str:
        return str(recipe.get("id") or recipe.get("codigo") or "")

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")


__all__ = ["RecetaDocumentacionBatchService"]
