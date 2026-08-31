from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext


class ErrorConfirmacionProcedimientoReceta(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class ConfirmacionProcedimientoRecetaService:
    REQUIRED_SCOPE = "recetas:write"

    def __init__(self, base_dir: Path, repository: RepositorioBibliotecaRecetas601 | None = None) -> None:
        self.repository = repository or RepositorioBibliotecaRecetas601(Path(base_dir))

    def preview(self, *, recipe_id: str, procedure: str, context: AuthorizedExecutionContext) -> dict[str, Any]:
        self._authorize(context)
        recipe = self._recipe(recipe_id)
        proposed = " ".join(str(procedure or "").split())
        if len(proposed) < 20:
            raise ErrorConfirmacionProcedimientoReceta("invalid_procedure", "La propuesta de procedimiento es demasiado corta.")
        current = str(recipe.get("elaboracion") or "").strip()
        token = self._token(recipe, proposed)
        unchanged = current == proposed
        return {
            "ok": True, "estado": "SIN_CAMBIOS" if unchanged else "LISTO_PARA_CONFIRMAR",
            "recipe_id": str(recipe.get("id") or ""), "nombre": str(recipe.get("nombre") or ""),
            "procedimiento_actual": current or None, "procedimiento_propuesto": proposed,
            "origen_propuesta": "IA", "preview_token": token, "requiere_confirmacion": not unchanged,
            "datos_reales_modificados": False,
        }

    def confirm(self, *, recipe_id: str, procedure: str, preview_token: str, context: AuthorizedExecutionContext) -> dict[str, Any]:
        preview = self.preview(recipe_id=recipe_id, procedure=procedure, context=context)
        if not preview_token or preview_token != preview["preview_token"]:
            raise ErrorConfirmacionProcedimientoReceta("stale_or_invalid_preview", "La vista previa ya no coincide con la receta.")
        if preview["estado"] == "SIN_CAMBIOS":
            return {**preview, "idempotente": True, "datos_reales_modificados": False}
        result = self.repository.editar(recipe_id, {"elaboracion": preview["procedimiento_propuesto"]})
        if not result.get("ok"):
            raise ErrorConfirmacionProcedimientoReceta("recipe_update_failed", "No se pudo guardar el procedimiento.")
        return {"ok": True, "estado": "CONFIRMADO", "recipe_id": recipe_id, "procedimiento": preview["procedimiento_propuesto"], "origen_propuesta": "IA", "idempotente": False, "datos_reales_modificados": True}

    def _authorize(self, context: AuthorizedExecutionContext) -> None:
        valid, _reason = context.validate() if isinstance(context, AuthorizedExecutionContext) else (False, "")
        if not valid or self.REQUIRED_SCOPE not in context.scopes:
            raise ErrorConfirmacionProcedimientoReceta("unauthorized", "El actor no está autorizado para guardar procedimientos.")

    def _recipe(self, recipe_id: str) -> dict[str, Any]:
        recipe = self.repository.obtener(recipe_id)
        if not recipe:
            raise ErrorConfirmacionProcedimientoReceta("recipe_not_found", "La receta no existe en la biblioteca editable.")
        return recipe

    @staticmethod
    def _token(recipe: dict[str, Any], procedure: str) -> str:
        payload = json.dumps({"id": recipe.get("id"), "version": recipe.get("version"), "actual": recipe.get("elaboracion"), "propuesto": procedure}, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = ["ConfirmacionProcedimientoRecetaService", "ErrorConfirmacionProcedimientoReceta"]