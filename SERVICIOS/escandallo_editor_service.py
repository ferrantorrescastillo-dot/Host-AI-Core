from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from SERVICIOS.biblioteca_escandallos_601 import BibliotecaEscandallos601
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext


class EscandalloEditorError(ValueError):
    def __init__(self, code: str, message: str): self.code = code; super().__init__(message)


class EscandalloEditorService:
    REQUIRED_SCOPE = "escandallos:write"

    def __init__(self, base_dir: Path, library: BibliotecaEscandallos601 | None = None) -> None:
        self.library = library or BibliotecaEscandallos601(base_dir)

    def preview(self, *, escandallo_id: str, changes: dict[str, Any], context: AuthorizedExecutionContext) -> dict[str, Any]:
        self._authorize(context)
        current = self.library.repo_esc.obtener(escandallo_id)
        if not current: raise EscandalloEditorError("escandallo_not_found", "Escandallo no encontrado.")
        proposed = self._proposed(current, changes)
        calculation = self.library.motor.calcular(
            nombre_escandallo=str(proposed.get("nombre") or current.get("nombre") or "Escandallo"),
            numero_raciones=float(proposed.get("numero_raciones") or 0), lineas_entrada=list(proposed["lineas"]),
            precio_venta_total=float(proposed.get("precio_venta_total") or 0), receta_asociada=dict(current.get("receta_asociada") or {}),
        )
        blocking = self._blocking(calculation)
        if blocking: raise EscandalloEditorError("invalid_lines", " | ".join(blocking))
        normalized = {**proposed, **calculation}
        token = self._token(current, normalized, context)
        return {"ok": True, "estado": "LISTO_PARA_CONFIRMAR", "escandallo_antes": current, "escandallo_propuesto": normalized, "preview_token": token, "requiere_confirmacion": True, "datos_reales_modificados": False}

    def confirm(self, *, escandallo_id: str, changes: dict[str, Any], preview_token: str, context: AuthorizedExecutionContext) -> dict[str, Any]:
        preview = self.preview(escandallo_id=escandallo_id, changes=changes, context=context)
        if not preview_token or preview_token != preview["preview_token"]: raise EscandalloEditorError("stale_or_invalid_preview", "La vista previa ya no es válida.")
        result = self.library.editar(escandallo_id, preview["escandallo_propuesto"])
        if not result.get("ok"): raise EscandalloEditorError("write_failed", str(result.get("mensaje") or "No se pudo guardar."))
        return {"ok": True, "estado": "CONFIRMADO", "escandallo": result["escandallo"], "datos_reales_modificados": True}

    def _proposed(self, current: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
        allowed = {"lineas", "numero_raciones", "rendimiento_total", "unidad_rendimiento"}
        unknown = set(changes) - allowed
        if unknown: raise EscandalloEditorError("unsupported_change", "Cambio no admitido: " + ", ".join(sorted(unknown)))
        proposed = {**current, **changes}
        lines = list(proposed.get("lineas") or [])
        if not lines: raise EscandalloEditorError("empty_lines", "El escandallo debe conservar al menos una línea.")
        seen = set()
        for line in lines:
            code = str(line.get("producto_codigo") or line.get("articulo_id") or "").strip()
            qty = line.get("cantidad_neta", line.get("cantidad"))
            try: valid_qty = float(qty) > 0
            except (TypeError, ValueError): valid_qty = False
            if not valid_qty: raise EscandalloEditorError("invalid_quantity", "Todas las cantidades deben ser mayores que cero.")
            if not str(line.get("unidad_receta") or line.get("unidad") or "").strip(): raise EscandalloEditorError("invalid_unit", "Todas las líneas requieren unidad.")
            if code:
                if code in seen: raise EscandalloEditorError("duplicate_article", "No se admiten artículos duplicados.")
                seen.add(code)
                if self.library.repo_prod.obtener_producto(code) is None: raise EscandalloEditorError("article_not_found", f"Artículo no encontrado: {code}.")
        if float(proposed.get("numero_raciones") or proposed.get("rendimiento_total") or 0) <= 0: raise EscandalloEditorError("invalid_yield", "El rendimiento debe ser mayor que cero.")
        return proposed

    @staticmethod
    def _blocking(calculation: dict[str, Any]) -> list[str]:
        return [str(i.get("detalle") or i.get("tipo")) for i in calculation.get("incidencias", []) if str(i.get("tipo") or "") in {"PRODUCTO_INEXISTENTE", "UNIDAD_INCOMPATIBLE", "CONVERSION_NO_DISPONIBLE", "CANTIDAD_INEXISTENTE"}]

    def _authorize(self, context: AuthorizedExecutionContext) -> None:
        valid, _ = context.validate() if isinstance(context, AuthorizedExecutionContext) else (False, "")
        if not valid or self.REQUIRED_SCOPE not in context.scopes: raise EscandalloEditorError("unauthorized", "El actor no está autorizado.")

    @staticmethod
    def _token(current: dict[str, Any], proposed: dict[str, Any], context: AuthorizedExecutionContext) -> str:
        raw = json.dumps({"current": current, "proposed": proposed, "actor": context.user_id, "tenant": context.tenant_id}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()


__all__ = ["EscandalloEditorService", "EscandalloEditorError"]
