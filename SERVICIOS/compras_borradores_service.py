from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from MOTORES.motor_compras import MotorCompras
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


class ComprasBorradoresService:
    def __init__(self, compras: MotorCompras, base_dir: Path | None = None) -> None:
        self.compras = compras
        self.productos = RepositorioProductosMaestro601(base_dir) if base_dir is not None else None

    def obtener(self, pedido_id: str) -> dict[str, Any]:
        pedido = self.compras.obtener_pedido(pedido_id)
        if not pedido:
            return self._error(404, "draft_not_found", "Borrador no encontrado.")
        data = self._serializar(pedido.to_dict())
        return {"ok": True, "borrador": data, "revision": self._revision(pedido.to_dict())}

    def actualizar(self, pedido_id: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            pedido = self.compras.actualizar_borrador_completo(pedido_id, body)
        except KeyError:
            return self._error(404, "draft_not_found", "Borrador no encontrado.")
        except (TypeError, ValueError) as exc:
            return self._error(400, "invalid_draft", str(exc))
        data = self._serializar(pedido.to_dict())
        return {"ok": True, "borrador": data, "revision": self._revision(pedido.to_dict())}

    def confirmar(self, pedido_id: str, body: dict[str, Any]) -> dict[str, Any]:
        pedido = self.compras.obtener_pedido(pedido_id)
        if not pedido:
            return self._error(404, "draft_not_found", "Borrador no encontrado.")
        if str(body.get("confirmacion") or "") != "CONFIRMAR_PEDIDO":
            return self._error(400, "confirmation_required", "Debes confirmar explícitamente la creación del pedido.")
        if pedido.estado == "preparado" and pedido.borrador_origen_id == pedido.id:
            confirmed, idempotent = self.compras.confirmar_borrador_pedido(pedido_id, usuario=str(body.get("usuario") or "web"))
            return self._confirmation_payload(confirmed.to_dict(), idempotent, [])
        revision = self._revision(pedido.to_dict())
        if revision["errores_bloqueantes"]:
            return {"ok": False, "error": {"status": 400, "code": "invalid_draft", "message": "El borrador contiene errores bloqueantes."}, "revision": revision}
        try:
            confirmed, idempotent = self.compras.confirmar_borrador_pedido(
                pedido_id,
                usuario=str(body.get("usuario") or "web"),
                actualizado_en=str(body.get("actualizado_en") or ""),
            )
        except RuntimeError as exc:
            return self._error(409, "draft_version_conflict", str(exc))
        except (TypeError, ValueError) as exc:
            return self._error(400, "invalid_draft", str(exc))
        return self._confirmation_payload(confirmed.to_dict(), idempotent, revision["advertencias"])

    def _revision(self, data: dict[str, Any]) -> dict[str, Any]:
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        provider = str(data.get("proveedor") or "").strip()
        active_providers = {
            str(item.get("nombre") or "").strip().casefold()
            for item in self.compras.listar_proveedores(incluir_inactivos=False)
        }
        if not provider or provider.casefold() not in active_providers:
            errors.append({"code": "invalid_provider", "field": "proveedor", "message": "Selecciona un proveedor activo existente."})
        lines = list(data.get("lineas") or [])
        if not lines:
            errors.append({"code": "empty_order", "field": "lineas", "message": "El borrador debe contener al menos una línea."})
        for index, line in enumerate(lines):
            article_id = str(line.get("articulo_id") or "").strip()
            if not article_id or (self.productos is not None and not self.productos.obtener_producto(article_id)):
                errors.append({"code": "invalid_article", "field": "articulo_id", "line_index": index, "message": "Selecciona un artículo existente."})
            try:
                quantity = float(line.get("cantidad") or 0)
            except (TypeError, ValueError):
                quantity = 0
            if quantity <= 0:
                errors.append({"code": "invalid_quantity", "field": "cantidad", "line_index": index, "message": "La cantidad debe ser mayor que cero."})
            if not str(line.get("unidad") or "").strip():
                errors.append({"code": "invalid_unit", "field": "unidad", "line_index": index, "message": "La unidad es obligatoria."})
            try:
                price = float(line.get("precio_unitario") or 0)
            except (TypeError, ValueError):
                price = 0
            if price <= 0:
                warnings.append({"code": "price_pending", "field": "precio_unitario", "line_index": index, "message": "La línea no tiene un precio estimado positivo."})
        return {"valido": not errors, "errores_bloqueantes": errors, "advertencias": warnings}

    def _confirmation_payload(self, data: dict[str, Any], idempotent: bool, warnings: list[dict[str, Any]]) -> dict[str, Any]:
        serialized = self._serializar(data)
        return {
            "ok": True, "pedido": serialized, "borrador": serialized,
            "idempotente": idempotent, "advertencias": warnings,
            "stock_modificado": False, "inventario_modificado": False, "recepciones_creadas": 0,
        }

    @staticmethod
    def _serializar(data: dict[str, Any]) -> dict[str, Any]:
        out = dict(data)
        if not out.get("origen_id"):
            match = re.search(r"Men[uú]\s+(\S+)\s+v(\d+).*?propuesta\s+(\S+)", str(out.get("observaciones") or ""), re.IGNORECASE)
            if match:
                out.update(origen_tipo="menu", origen_id=match.group(1), origen_version=int(match.group(2)), propuesta_id=match.group(3))
        out["origen"] = {"tipo": out.get("origen_tipo") or "manual", "id": out.get("origen_id") or "", "version": int(out.get("origen_version") or 0), "propuesta_id": out.get("propuesta_id") or ""}
        return out

    @staticmethod
    def _error(status: int, code: str, message: str) -> dict[str, Any]:
        return {"ok": False, "error": {"status": status, "code": code, "message": message}}
