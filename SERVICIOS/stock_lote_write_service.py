from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.stock_locations import STOCK_LOCATIONS, canonical_location_id, location_name


class StockLoteWriteError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class StockLoteWriteService:
    """Acciones tipadas sobre lotes; delega la persistencia al MotorStock."""

    REQUIRED_SCOPE = "stock:write"
    PREVIEW_SCOPE = "stock:preview"
    TTL_SECONDS = 900

    def __init__(self, core: Any) -> None:
        self.core = core
        self._pending: dict[str, dict[str, Any]] = {}
        self._pending_by_session: dict[str, str] = {}
        self._consumed: dict[str, dict[str, Any]] = {}

    def detail(self, lot_id: str) -> dict[str, Any]:
        lot = self._lot(lot_id)
        data = lot.to_dict()
        related = []
        for movement in self.core.stock.movimientos.values():
            item = movement.to_dict()
            trace = dict(item.get("trazabilidad") or {})
            if str(item.get("lote_id") or trace.get("lote_id") or trace.get("lote") or "") == lot_id:
                related.append(item)
        return {"ok": True, "lote": data, "incidencias": self._incidents(data), "movimientos": related, "acciones": self._actions(data)}

    def locations(self) -> dict[str, Any]:
        values: dict[str, list[dict[str, Any]]] = {item["id"]: [] for item in STOCK_LOCATIONS}
        for lot in self.core.stock.lotes.values():
            location = canonical_location_id(lot.ubicacion)
            if location:
                values.setdefault(location, []).append(lot.to_dict())
        return {"ok": True, "ubicaciones": [{"id": item["id"], "nombre": item["nombre"], "lotes": values[item["id"]], "total_lotes": len(values[item["id"]]), "total_articulos": len({str(lot.get("articulo_id") or lot.get("nombre") or "") for lot in values[item["id"]]})} for item in STOCK_LOCATIONS]}

    def preview_location(self, *, lot_id: str, location_id: str, context: AuthorizedExecutionContext, session_id: str = "web") -> dict[str, Any]:
        self._authorize(context, preview=True)
        lot = self._lot(lot_id)
        destination = canonical_location_id(location_id)
        allowed = {item["id"] for item in self.locations()["ubicaciones"]}
        if not destination or destination not in allowed:
            raise StockLoteWriteError("invalid_location", "Selecciona una ubicación canónica existente.")
        before = lot.to_dict()
        after = {**before, "ubicacion": destination, "ubicacion_nombre": location_name(destination)}
        unchanged = canonical_location_id(before.get("ubicacion")) == destination
        token = self._token(lot_id, before, destination, context)
        session = str(session_id or "web")
        previous = self._pending_by_session.get(session)
        if previous: self._pending.pop(previous, None)
        self._pending[token] = {"lot_id": lot_id, "location_id": destination, "session_id": session, "expires_at": time.monotonic() + self.TTL_SECONDS}
        self._pending_by_session[session] = token
        return {"ok": True, "estado": "SIN_CAMBIOS" if unchanged else "LISTO_PARA_CONFIRMAR", "operacion": "CAMBIAR_UBICACION", "lote_antes": before, "lote_despues": after, "preview_token": token, "requiere_confirmacion": not unchanged, "datos_reales_modificados": False}

    def confirm_location(self, *, lot_id: str, location_id: str, preview_token: str, context: AuthorizedExecutionContext, session_id: str = "web") -> dict[str, Any]:
        self._authorize(context, preview=False)
        if preview_token in self._consumed: return dict(self._consumed[preview_token])
        pending = self._pending.get(str(preview_token or ""))
        if not pending or pending["session_id"] != str(session_id or "web"):
            raise StockLoteWriteError("stale_or_invalid_preview", "La vista previa ya no corresponde al lote actual.")
        if float(pending["expires_at"]) < time.monotonic():
            self._remove_pending(preview_token); raise StockLoteWriteError("expired_preview", "La vista previa ha caducado.")
        destination = canonical_location_id(location_id)
        if pending["lot_id"] != lot_id or pending["location_id"] != destination:
            raise StockLoteWriteError("stale_or_invalid_preview", "La vista previa no corresponde a esta operación.")
        lot = self._lot(lot_id); before = lot.to_dict()
        expected = self._token(lot_id, before, destination, context)
        if expected != preview_token: raise StockLoteWriteError("stale_or_invalid_preview", "El lote ha cambiado desde la vista previa.")
        preview = {"requiere_confirmacion": canonical_location_id(before.get("ubicacion")) != destination, "lote_antes": before}
        if not preview["requiere_confirmacion"]:
            result = {"ok": True, "estado": "SIN_CAMBIOS", "lote": before, "idempotente": True, "datos_reales_modificados": False}; self._remove_pending(preview_token); self._consumed[preview_token] = result; return result
        quantity = float(preview["lote_antes"]["cantidad"])
        result = self.core.stock.actualizar_lote(lot_id, ubicacion=destination)
        if not result.get("ok"):
            raise StockLoteWriteError("write_failed", str(result.get("mensaje") or "No se pudo actualizar el lote."))
        persisted = self._lot(lot_id).to_dict()
        if float(persisted["cantidad"]) != quantity:
            raise StockLoteWriteError("stock_invariant_failed", "La ubicación no puede modificar la cantidad del lote.")
        result = {"ok": True, "estado": "CONFIRMADO", "lote": persisted, "idempotente": False, "datos_reales_modificados": True}
        self._remove_pending(preview_token); self._consumed[preview_token] = result
        return result

    def discard_location(self, *, preview_token: str, context: AuthorizedExecutionContext, session_id: str = "web") -> dict[str, Any]:
        self._authorize(context, preview=True)
        pending = self._pending.get(str(preview_token or ""))
        if not pending or pending["session_id"] != str(session_id or "web"): raise StockLoteWriteError("stale_or_invalid_preview", "La vista previa ya no está disponible.")
        self._remove_pending(preview_token)
        return {"ok": True, "estado": "DESCARTADO", "datos_reales_modificados": False}

    def _remove_pending(self, token: str) -> None:
        pending = self._pending.pop(str(token or ""), None)
        if pending and self._pending_by_session.get(pending["session_id"]) == token: self._pending_by_session.pop(pending["session_id"], None)

    def _authorize(self, context: AuthorizedExecutionContext, *, preview: bool) -> None:
        if not isinstance(context, AuthorizedExecutionContext):
            raise StockLoteWriteError("unauthorized", "Falta contexto autorizado.")
        valid, _ = context.validate()
        required = self.PREVIEW_SCOPE if preview else self.REQUIRED_SCOPE
        if not valid or (required not in context.scopes and not (preview and self.REQUIRED_SCOPE in context.scopes)):
            raise StockLoteWriteError("unauthorized", "El actor no está autorizado.")

    def _lot(self, lot_id: str) -> Any:
        key = str(lot_id or "").strip()
        if not key or any(char in key for char in ("/", "\\")):
            raise StockLoteWriteError("invalid_lot_id", "Identificador de lote no válido.")
        lot = self.core.stock.lotes.get(key)
        if lot is None:
            raise StockLoteWriteError("lot_not_found", "Lote no encontrado.")
        return lot

    @staticmethod
    def _incidents(data: dict[str, Any]) -> list[dict[str, str]]:
        out = []
        if not str(data.get("ubicacion") or "").strip(): out.append({"code": "SIN_UBICACION", "message": "El lote no tiene ubicación."})
        if float(data.get("cantidad") or 0) <= 0: out.append({"code": "SIN_STOCK", "message": "El lote no tiene cantidad disponible."})
        return out

    @staticmethod
    def _actions(data: dict[str, Any]) -> list[str]:
        return ["CAMBIAR_UBICACION", "REGISTRAR_AJUSTE"] if float(data.get("cantidad") or 0) > 0 else ["REGISTRAR_AJUSTE"]

    @staticmethod
    def _token(lot_id: str, before: dict[str, Any], destination: str, context: AuthorizedExecutionContext) -> str:
        raw = json.dumps({"lot_id": lot_id, "before": before, "destination": destination, "actor": context.user_id, "tenant": context.tenant_id}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


__all__ = ["StockLoteWriteService", "StockLoteWriteError"]
