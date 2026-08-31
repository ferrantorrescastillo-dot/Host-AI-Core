from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from SERVICIOS.articulo_economico_canonico import convert_quantity
from SERVICIOS.host_ai_compras_read_service import HostAIComprasReadService
from SERVICIOS.menu_necesidades_service import MenuNecesidadesService


class HostAIOperationalNeedsReadService:
    """Adapta necesidades canónicas y cobertura confirmada a una READ conversacional."""

    CONFIRMED = {"preparado", "enviado", "parcialmente_recibido"}

    def __init__(self, base_dir: Path, core: Any | None = None, needs: Any | None = None, purchases: Any | None = None) -> None:
        self.needs = needs or MenuNecesidadesService(
            Path(base_dir), compras=getattr(core, "compras", None), stock_motor=getattr(core, "stock", None),
        )
        self.purchases = purchases if purchases is not None else HostAIComprasReadService(core) if core is not None else None

    def consultar_menu(self, menu_id: str) -> dict[str, Any]:
        result = dict(self.needs.necesidades(str(menu_id or "")) or {})
        if not result.get("ok") or not isinstance(result.get("necesidades"), dict):
            return {"estado": "NO_ENCONTRADO", "menu_id": str(menu_id or ""),
                    "datos_reales_modificados": False}
        needs = dict(result["necesidades"])
        confirmed, drafts, orders = self._purchase_coverage()
        lines = []
        for source in list(needs.get("lines") or []):
            if not isinstance(source, dict):
                continue
            line = dict(source)
            article_id = str(line.get("articulo_id") or "")
            unit = str(line.get("unidad_necesaria") or "")
            missing = self._number(line.get("cantidad_faltante"))
            incoming = confirmed.get((article_id, unit), 0.0)
            net = None if missing is None else max(missing - incoming, 0.0)
            purchase_quantity = None if net is None else MenuNecesidadesService._purchase_quantity(
                net, self._number(line.get("cantidad_formato")),
            )
            pack = self._number(line.get("cantidad_formato"))
            price = self._number(line.get("precio_estimado"))
            price_unit = str(line.get("unidad_precio") or "").strip()
            net_in_price_unit = convert_quantity(net, unit, price_unit, line) if net is not None and price_unit else None
            line["compras_confirmadas_pendientes"] = round(incoming, 6)
            line["necesidad_neta"] = round(net, 6) if net is not None else None
            line["cantidad_compra_neta"] = purchase_quantity
            line["cantidad_formatos_neta"] = (
                round(purchase_quantity / pack, 6)
                if purchase_quantity is not None and pack not in (None, 0) else None
            )
            line["coste_estimado_neto"] = (
                round(price * purchase_quantity, 4)
                if price is not None and purchase_quantity is not None else None
            )
            line["precio_unitario"] = price
            line["unidad_precio"] = price_unit or None
            line["coste_neto"] = price * float(net_in_price_unit) if price is not None and net_in_price_unit is not None else None
            line["borradores_pendientes"] = round(drafts.get((article_id, unit), 0.0), 6)
            line["requiere_compra"] = bool(net is not None and net > 0)
            lines.append(line)
        needs["lines"] = lines
        needs["summary"] = {
            **dict(needs.get("summary") or {}),
            "compra_neta": sum(bool(line.get("requiere_compra")) for line in lines),
            "cubiertos_total": sum(line.get("necesidad_neta") == 0 for line in lines),
        }
        return {"estado": "OK", "necesidades": needs, "pedidos": orders,
                "formula": "NECESIDAD_REAL - STOCK_UTILIZABLE - COMPRAS_CONFIRMADAS_PENDIENTES",
                "borradores_cuentan_como_cobertura": False, "solo_lectura": True,
                "datos_reales_modificados": False}

    def _purchase_coverage(self) -> tuple[dict[tuple[str, str], float], dict[tuple[str, str], float], list[dict[str, Any]]]:
        confirmed, drafts = defaultdict(float), defaultdict(float)
        if self.purchases is None:
            return {}, {}, []
        if hasattr(self.purchases, "consultar_cobertura_articulos"):
            orders = list(self.purchases.consultar_cobertura_articulos() or [])
        else:
            orders = list(self.purchases.consultar_pedidos(solo_abiertos=True, limite=10).get("pedidos") or [])
        for order in orders:
            state = str(order.get("estado") or "").lower()
            target = confirmed if state in self.CONFIRMED else drafts if state == "borrador" else None
            if target is None:
                continue
            for line in list(order.get("lineas") or []):
                key = (str(line.get("articulo_id") or ""), str(line.get("unidad") or ""))
                if key[0] and key[1]:
                    target[key] += float(line.get("pendiente") or 0)
        return dict(confirmed), dict(drafts), [dict(order) for order in orders if isinstance(order, dict)]

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            return float(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None


__all__ = ["HostAIOperationalNeedsReadService"]
