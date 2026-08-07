from __future__ import annotations

import re
from typing import Any

from MOTORES.motor_compras import MotorCompras


class ComprasBorradoresService:
    def __init__(self, compras: MotorCompras) -> None:
        self.compras = compras

    def obtener(self, pedido_id: str) -> dict[str, Any]:
        pedido = self.compras.obtener_pedido(pedido_id)
        if not pedido:
            return self._error(404, "draft_not_found", "Borrador no encontrado.")
        return {"ok": True, "borrador": self._serializar(pedido.to_dict())}

    def actualizar(self, pedido_id: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            pedido = self.compras.actualizar_borrador_completo(pedido_id, body)
        except KeyError:
            return self._error(404, "draft_not_found", "Borrador no encontrado.")
        except (TypeError, ValueError) as exc:
            return self._error(400, "invalid_draft", str(exc))
        return {"ok": True, "borrador": self._serializar(pedido.to_dict())}

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
