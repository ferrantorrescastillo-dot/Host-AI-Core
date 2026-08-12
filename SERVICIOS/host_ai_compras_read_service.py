from __future__ import annotations

import unicodedata
from typing import Any


class HostAIComprasReadService:
    """Proyección conversacional, saneada y de solo lectura, de Compras."""

    LIMIT = 10

    def __init__(self, core: Any) -> None:
        self.compras = core.compras

    def consultar_pedidos(self, estado: str = "", proveedor: str = "", pendientes_recepcion: bool = False, solo_abiertos: bool = False) -> dict[str, Any]:
        pedidos = list(self.compras.listar_pedidos() or [])
        projected = [self._pedido(item) for item in pedidos]
        if estado:
            projected = [item for item in projected if self._norm(item["estado"]) == self._norm(estado)]
        elif solo_abiertos:
            projected = [item for item in projected if self._norm(item["estado"]) not in {"recibido", "cancelado"}]
        if proveedor:
            projected = [item for item in projected if self._norm(proveedor) in self._norm(item["proveedor_nombre"])]
        if pendientes_recepcion:
            projected = [item for item in projected if item["pendiente_recepcion"]]
        return self._dto("pedidos", pedidos=projected)

    def consultar_propuestas(self) -> dict[str, Any]:
        items = list(self.compras.listar_propuestas_compra(solo_pendientes=True) or [])
        propuestas = [{
            "propuesta_id": str(item.get("id") or ""), "producto": str(item.get("producto") or ""),
            "cantidad": self._number(item.get("comprar")), "unidad": str(item.get("unidad") or ""),
            "estado": str(item.get("estado") or ""), "proveedor_sugerido": str(item.get("proveedor_sugerido") or ""),
            "fecha": str(item.get("creado_en") or ""),
        } for item in items]
        return self._dto("propuestas", propuestas=propuestas)

    def consultar_necesidades(self) -> dict[str, Any]:
        items = list(self.compras.listar_necesidades(solo_pendientes=True) or [])
        necesidades = [{
            "necesidad_id": str(item.get("id") or ""), "articulo_id": str(item.get("articulo_id") or ""),
            "nombre": str(item.get("nombre") or ""), "cantidad": self._number(item.get("cantidad")),
            "unidad": str(item.get("unidad") or ""), "estado": str(item.get("estado") or ""),
            "prioridad": int(item.get("prioridad") or 0), "fecha_necesaria": str(item.get("fecha_necesaria") or ""),
        } for item in items]
        return self._dto("necesidades", necesidades=necesidades)

    def buscar_por_proveedor(self, termino: str) -> dict[str, Any]:
        termino = str(termino or "").strip()
        proveedores = list(self.compras.listar_proveedores(incluir_inactivos=False, texto=termino) or [])
        safe = [{"proveedor_id": str(item.get("id") or ""), "nombre": str(item.get("nombre") or ""), "estado": str(item.get("estado") or "")} for item in proveedores]
        exact = [item for item in safe if self._norm(item["nombre"]) == self._norm(termino)]
        if len(exact) == 1:
            selected = exact[0]
        elif len(safe) == 1:
            selected = safe[0]
        else:
            state = "AMBIGUO" if safe else "NO_ENCONTRADO"
            return self._dto("proveedor", estado=state, proveedores=safe)
        pedidos = self.consultar_pedidos(proveedor=selected["nombre"])["pedidos"]
        return self._dto("proveedor", pedidos=pedidos, proveedores=[selected])

    def _pedido(self, item: dict[str, Any]) -> dict[str, Any]:
        order_id = str(item.get("id") or "")
        received: dict[str, float] = {}
        for reception in list(self.compras.listar_recepciones(pedido_id=order_id) or []):
            if self._norm(reception.get("estado")) != "confirmada":
                continue
            for line in list(reception.get("lineas") or []):
                key = str(line.get("order_line_id") or "")
                received[key] = received.get(key, 0.0) + float(line.get("received_quantity") or 0)
        lines = []
        pending_any = False
        for line in list(item.get("lineas") or []):
            line_id = str(line.get("id") or "")
            ordered = float(line.get("cantidad") or 0)
            received_qty = min(ordered, received.get(line_id, 0.0))
            pending = max(0.0, round(ordered - received_qty, 6))
            pending_any = pending_any or pending > 0
            lines.append({"articulo_id": str(line.get("articulo_id") or ""), "nombre": str(line.get("nombre") or ""), "pedido": ordered, "recibido": received_qty, "pendiente": pending, "unidad": str(line.get("unidad") or "")})
        total = sum(float(line.get("cantidad") or 0) * float(line.get("precio_unitario") or 0) for line in list(item.get("lineas") or []))
        return {"pedido_id": order_id, "proveedor_nombre": str(item.get("proveedor") or ""), "estado": str(item.get("estado") or ""), "fecha": str(item.get("fecha") or item.get("creado_en") or ""), "total": round(total, 2), "numero_lineas": len(lines), "pendiente_recepcion": pending_any and self._norm(item.get("estado")) not in {"borrador", "cancelado", "recibido"}, "lineas": lines}

    def _dto(self, consulta: str, *, estado: str | None = None, pedidos: list | None = None, propuestas: list | None = None, necesidades: list | None = None, proveedores: list | None = None) -> dict[str, Any]:
        pedidos = list(pedidos or [])[: self.LIMIT]; propuestas = list(propuestas or [])[: self.LIMIT]
        necesidades = list(necesidades or [])[: self.LIMIT]; proveedores = list(proveedores or [])[: self.LIMIT]
        total = len(pedidos) + len(propuestas) + len(necesidades) + len(proveedores)
        return {"estado": estado or ("OK" if total else "VACIO"), "consulta": consulta,
                "resumen": {"total": total, "preparados": sum(self._norm(x.get("estado")) == "preparado" for x in pedidos), "parcialmente_recibidos": sum(self._norm(x.get("estado")) == "parcialmente_recibido" for x in pedidos), "recibidos": sum(self._norm(x.get("estado")) == "recibido" for x in pedidos), "pendientes_recepcion": sum(bool(x.get("pendiente_recepcion")) for x in pedidos)},
                "pedidos": pedidos, "propuestas": propuestas, "necesidades": necesidades, "proveedores": proveedores,
                "fuente": "compras_canonico", "solo_lectura": True, "datos_reales_modificados": False}

    @staticmethod
    def _number(value: Any) -> float | None:
        try: return float(value)
        except (TypeError, ValueError): return None

    @staticmethod
    def _norm(value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or "").strip().lower())
        return "".join(char for char in text if not unicodedata.combining(char))


__all__ = ["HostAIComprasReadService"]
