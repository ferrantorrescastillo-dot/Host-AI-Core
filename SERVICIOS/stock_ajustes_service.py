from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


class StockAjusteError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class StockAjustesService:
    """Valida y delega inventarios/ajustes al ledger canónico de Stock."""

    TIPOS = {"INVENTARIO_INICIAL", "AJUSTE_POSITIVO", "AJUSTE_NEGATIVO"}
    CONFIRMACION = "REGISTRAR_MOVIMIENTO_STOCK"
    TTL_SECONDS = 900

    def __init__(self, core: Any) -> None:
        self.stock = core.stock
        self.productos = RepositorioProductosMaestro601(core.base_dir)
        self._pending: dict[str, dict[str, Any]] = {}
        self._consumed: dict[str, dict[str, Any]] = {}

    def preview(self, body: dict[str, Any], context: AuthorizedExecutionContext) -> dict[str, Any]:
        self._authorize(context, "stock:preview")
        normalized = self._normalize_adjustment(body)
        before = self._current(normalized)
        target = normalized["cantidad_objetivo"]
        difference = target - before
        token = self._token(normalized, before, context)
        self._pending[token] = {
            "payload": normalized,
            "stock_anterior": before,
            "expires_at": time.monotonic() + self.TTL_SECONDS,
            "actor": context.user_id,
            "tenant": context.tenant_id,
        }
        return {
            "ok": True,
            "operacion": "AJUSTAR_STOCK",
            "preview_token": token,
            "stock_anterior": before,
            "stock_resultante": target,
            "diferencia": difference,
            "unidad": normalized["unidad"],
            "motivo": normalized["motivo"],
            "requiere_confirmacion": abs(difference) > 1e-9,
            "datos_reales_modificados": False,
        }

    def confirm(self, body: dict[str, Any], context: AuthorizedExecutionContext) -> dict[str, Any]:
        self._authorize(context, "stock:write")
        token = str(body.get("preview_token") or "")
        if token in self._consumed:
            return {**self._consumed[token], "idempotente": True}
        pending = self._pending.get(token)
        if not pending or pending["actor"] != context.user_id or pending["tenant"] != context.tenant_id:
            raise StockAjusteError("stale_or_invalid_preview", "La vista previa ya no está disponible.")
        if float(pending["expires_at"]) < time.monotonic():
            self._pending.pop(token, None)
            raise StockAjusteError("expired_preview", "La vista previa ha caducado.")
        payload = dict(pending["payload"])
        current = self._current(payload)
        if abs(current - float(pending["stock_anterior"])) > 1e-9 or self._token(payload, current, context) != token:
            self._pending.pop(token, None)
            raise StockAjusteError("stale_or_invalid_preview", "El stock ha cambiado desde la vista previa.")
        difference = float(payload["cantidad_objetivo"]) - current
        if abs(difference) <= 1e-9:
            result = {"ok": True, "estado": "SIN_CAMBIOS", "stock_anterior": current, "stock_actual": current, "movimiento": None, "datos_reales_modificados": False, "idempotente": True}
        else:
            movement = {
                "article_id": payload["article_id"],
                "tipo": "AJUSTE_POSITIVO" if difference > 0 else "AJUSTE_NEGATIVO",
                "cantidad": abs(difference),
                "unidad": payload["unidad"],
                "observaciones": payload["motivo"],
                "usuario": context.user_id,
                "confirmacion": self.CONFIRMACION,
            }
            result = self.registrar(movement)
            if not result.get("ok"):
                raise StockAjusteError(str((result.get("error") or {}).get("code") or "write_failed"), str((result.get("error") or {}).get("message") or "No se pudo registrar el ajuste."))
            result = {**result, "estado": "CONFIRMADO", "idempotente": False}
        self._pending.pop(token, None)
        self._consumed[token] = dict(result)
        return result

    def discard(self, body: dict[str, Any], context: AuthorizedExecutionContext) -> dict[str, Any]:
        self._authorize(context, "stock:preview")
        token = str(body.get("preview_token") or "")
        pending = self._pending.get(token)
        if not pending or pending["actor"] != context.user_id or pending["tenant"] != context.tenant_id:
            raise StockAjusteError("stale_or_invalid_preview", "La vista previa ya no está disponible.")
        self._pending.pop(token, None)
        return {"ok": True, "estado": "DESCARTADO", "datos_reales_modificados": False}

    def _normalize_adjustment(self, body: dict[str, Any]) -> dict[str, Any]:
        article_id = str(body.get("article_id") or "").strip()
        article = self.productos.obtener_producto(article_id)
        if not article:
            raise StockAjusteError("article_not_found", "El artículo seleccionado no existe.")
        unit = str(body.get("unidad") or "").strip()
        canonical = str(article.get("unidad_base") or article.get("unidad") or "").strip()
        if not unit or unit.casefold() != canonical.casefold():
            raise StockAjusteError("invalid_unit", f"Usa la unidad base del artículo: {canonical or 'no definida'}.")
        try:
            target = float(body.get("cantidad_objetivo"))
        except (TypeError, ValueError):
            target = -1
        if target < 0:
            raise StockAjusteError("invalid_quantity", "La cantidad real no puede ser negativa.")
        reason = str(body.get("motivo") or "").strip()
        if not reason:
            raise StockAjusteError("reason_required", "Indica el motivo obligatorio del ajuste.")
        return {"article_id": article_id, "nombre": str(article.get("nombre") or article_id), "unidad": canonical, "cantidad_objetivo": target, "motivo": reason}

    def _current(self, payload: dict[str, Any]) -> float:
        return float(self.stock._cantidad_disponible(payload["nombre"], payload["article_id"], payload["unidad"]))

    @staticmethod
    def _authorize(context: AuthorizedExecutionContext, scope: str) -> None:
        if not isinstance(context, AuthorizedExecutionContext):
            raise StockAjusteError("unauthorized", "Falta contexto autorizado.")
        valid, _ = context.validate()
        if not valid or (scope not in context.scopes and not (scope == "stock:preview" and "stock:write" in context.scopes)):
            raise StockAjusteError("unauthorized", "El actor no está autorizado.")

    @staticmethod
    def _token(payload: dict[str, Any], current: float, context: AuthorizedExecutionContext) -> str:
        raw = json.dumps({"payload": payload, "stock_anterior": current, "actor": context.user_id, "tenant": context.tenant_id}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def registrar(self, body: dict[str, Any]) -> dict[str, Any]:
        if body.get("confirmacion") != self.CONFIRMACION:
            return self._error(400, "confirmation_required", "Confirma explícitamente el movimiento de Stock.")
        article_id = str(body.get("article_id") or "").strip()
        article = self.productos.obtener_producto(article_id)
        if not article:
            return self._error(404, "article_not_found", "El artículo seleccionado no existe.")
        movement_type = str(body.get("tipo") or "").strip().upper()
        if movement_type not in self.TIPOS:
            return self._error(400, "invalid_movement_type", "El tipo de movimiento no es válido.")
        try:
            quantity = float(body.get("cantidad"))
        except (TypeError, ValueError):
            quantity = 0.0
        if quantity <= 0:
            return self._error(400, "invalid_quantity", "La cantidad debe ser mayor que cero.")
        unit = str(body.get("unidad") or "").strip()
        canonical_unit = str(article.get("unidad_base") or article.get("unidad") or "").strip()
        if not unit or not canonical_unit or unit.casefold() != canonical_unit.casefold():
            return self._error(400, "invalid_unit", f"Usa la unidad base del artículo: {canonical_unit or 'no definida'}.")

        name = str(article.get("nombre") or article_id)
        current = self.stock._cantidad_disponible(name, article_id, canonical_unit)
        trace = {
            "origen": "ajuste_manual" if movement_type != "INVENTARIO_INICIAL" else "inventario_inicial",
            "usuario": str(body.get("usuario") or "web"), "observaciones": str(body.get("observaciones") or ""),
            "signo": 1 if movement_type != "AJUSTE_NEGATIVO" else -1,
            "production_plan_id": str(body.get("production_plan_id") or ""),
            "return_to": str(body.get("return_to") or ""),
            "lote": str(body.get("lote") or ""), "ubicacion": str(body.get("ubicacion") or ""),
            "caducidad": str(body.get("caducidad") or ""),
        }
        if movement_type == "INVENTARIO_INICIAL" and current > 0 and not body.get("confirmar_existente"):
            return self._error(409, "initial_inventory_exists", "El artículo ya tiene inventario. Confirma la corrección o utiliza un ajuste.", {"stock_actual": current, "unidad": canonical_unit})
        if movement_type == "AJUSTE_NEGATIVO" and current + 1e-9 < quantity:
            return self._error(409, "negative_stock_blocked", "El ajuste dejaría el Stock negativo.", {"stock_actual": current, "cantidad_solicitada": quantity, "unidad": canonical_unit})

        if movement_type == "INVENTARIO_INICIAL" and current > 0:
            result = self.stock.ajustar_inventario(name, quantity, canonical_unit, articulo_id=article_id,
                                                   familia=str(article.get("familia") or ""), ubicacion=str(body.get("ubicacion") or ""),
                                                   motivo=str(body.get("observaciones") or "Corrección de inventario inicial"))
            trace["signo"] = 1 if float(result.get("diferencia") or 0) > 0 else -1
            movement = dict((result.get("resultado") or {}).get("movimiento") or result.get("movimiento") or {})
            if not movement:
                return {"ok": True, "movimiento": None, "stock_anterior": current, "stock_actual": current,
                        "mensaje": "El inventario ya coincide con la cantidad indicada.", "datos_reales_modificados": False}
        elif movement_type in {"INVENTARIO_INICIAL", "AJUSTE_POSITIVO"}:
            result = self.stock.registrar_entrada(name, quantity, canonical_unit,
                familia=str(article.get("familia") or ""), ubicacion=str(body.get("ubicacion") or ""),
                articulo_id=article_id, caducidad=str(body.get("caducidad") or ""),
                motivo=str(body.get("observaciones") or movement_type.replace("_", " ").title()), trazabilidad=trace)
            movement = dict(result["movimiento"])
            self._retag(movement["id"], movement_type.lower(), trace)
        else:
            result = self.stock.consumir(name, quantity, canonical_unit,
                motivo=str(body.get("observaciones") or "Ajuste negativo manual"), articulo_id=article_id, trazabilidad=trace)
            movement = dict(result["movimiento"])
            self._retag(movement["id"], "ajuste_negativo", trace)

        if movement.get("id") in self.stock.movimientos:
            self._retag(movement["id"], str(self.stock.movimientos[movement["id"]].tipo), trace)
            movement = self.stock.movimientos[movement["id"]].to_dict()
        updated = self.stock._cantidad_disponible(name, article_id, canonical_unit)
        return {"ok": True, "movimiento": {**movement, "movement_id": movement.get("id"), "article_id": article_id,
                "signo": trace["signo"], "usuario": trace["usuario"], "observaciones": trace["observaciones"],
                "origen": trace["origen"]}, "stock_anterior": current, "stock_actual": updated,
                "mensaje": "Movimiento registrado correctamente.", "datos_reales_modificados": True,
                "pedidos_creados": 0, "recepciones_creadas": 0}

    def _retag(self, movement_id: str, movement_type: str, trace: dict[str, Any]) -> None:
        movement = self.stock.movimientos[movement_id]
        movement.tipo = movement_type
        movement.trazabilidad = {**dict(movement.trazabilidad or {}), **trace}
        self.stock._guardar_automatico()

    @staticmethod
    def _error(status: int, code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        return {"ok": False, "error": {"status": status, "code": code, "message": message}, "resultado": details or {}}


__all__ = ["StockAjustesService", "StockAjusteError"]
