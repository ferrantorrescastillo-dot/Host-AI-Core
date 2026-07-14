from __future__ import annotations

"""
Servicio Host AI 3.0.5.1 - Analizador Inteligente de Stock.

Responsabilidad:
- Leer el estado actual del stock.
- Detectar artículos sin stock, bajo mínimo, exceso, sin movimiento o sin ubicación.
- Calcular valoración estimada y resumen operativo.
"""

import json
from datetime import date, datetime
from typing import Any, Dict, List

from MODELOS.analisis_inteligente_stock import (
    InformeAnalisisInteligenteStock,
    ItemAnalisisStock,
)


class AnalizadorInteligenteStock:
    """Analiza el estado actual del stock y devuelve un informe operativo."""

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.stock_dir = self.base_dir / "DATOS" / "stock"
        self.stock_dir.mkdir(parents=True, exist_ok=True)

    def analizar_stock(self, dias_sin_movimiento: int = 30) -> Dict[str, Any]:
        stock = getattr(self.core, "stock", None)
        actual = stock.stock_actual() if stock else {"items": [], "total_lotes": 0}
        movimientos = stock.movimientos_listado() if stock else []
        movimientos_por_clave = self._agrupar_movimientos(movimientos)

        items: List[Dict[str, Any]] = []
        valor_total = 0.0
        contadores = self._crear_contadores()

        for item in actual.get("items", []):
            item_analizado, valor = self._analizar_item(
                item=item,
                stock=stock,
                movimientos_por_clave=movimientos_por_clave,
                dias_sin_movimiento=dias_sin_movimiento,
                contadores=contadores,
            )
            items.append(item_analizado)
            valor_total += valor

        items.sort(key=lambda item: (self._prioridad_estado(item["estado"]), -item["valor_estimado"], item["nombre"]))
        resumen = {**contadores, "estado_general": "revisar" if any(contadores.values()) else "ok"}
        lectura = (
            f"Análisis inteligente de stock: {len(items)} artículos, "
            f"{actual.get('total_lotes', 0)} lotes y valor estimado {round(valor_total, 2)} €."
        )

        return InformeAnalisisInteligenteStock(
            total_articulos=len(items),
            total_lotes=int(actual.get("total_lotes", 0) or 0),
            valor_total_estimado=round(valor_total, 4),
            articulos_sin_stock=contadores["sin_stock"],
            articulos_stock_bajo=contadores["stock_bajo"],
            articulos_exceso_stock=contadores["exceso_stock"],
            articulos_criticos=contadores["criticos"],
            articulos_sin_movimiento=contadores["sin_movimiento"],
            articulos_sin_ubicacion=contadores["sin_ubicacion"],
            items=items,
            resumen=resumen,
            lectura_host_ai=lectura,
        ).to_dict()

    def exportar_analisis(self, analisis: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        destino = self.stock_dir / (nombre or "analisis_inteligente_stock.json")
        destino.write_text(json.dumps(analisis, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "archivo": str(destino),
            "lectura_host_ai": f"Análisis inteligente de stock exportado: {destino.name}.",
        }

    def _analizar_item(
        self,
        item: Dict[str, Any],
        stock,
        movimientos_por_clave: Dict[str, List[Dict[str, Any]]],
        dias_sin_movimiento: int,
        contadores: Dict[str, int],
    ) -> tuple[Dict[str, Any], float]:
        clave = item.get("articulo_id") or item.get("clave") or item.get("nombre", "").lower().strip()
        cantidad = float(item.get("cantidad", 0) or 0)
        lotes = item.get("lotes", []) or []
        minimo = float(getattr(stock, "stock_minimos", {}).get(clave, 0) or 0) if stock else 0.0
        maximo = self._calcular_maximo(minimo, cantidad)
        valor = self._valorar_lotes(lotes)
        ubicaciones = self._extraer_ubicaciones(lotes)
        movimientos = movimientos_por_clave.get(clave, [])
        dias = self._dias_desde_ultimo_movimiento(movimientos)

        estado, motivos = self._evaluar_estado_item(
            cantidad=cantidad,
            minimo=minimo,
            maximo=maximo,
            ubicaciones=ubicaciones,
            dias=dias,
            dias_sin_movimiento=dias_sin_movimiento,
            contadores=contadores,
        )

        item_analizado = ItemAnalisisStock(
            clave=clave,
            nombre=item.get("nombre", clave),
            articulo_id=item.get("articulo_id", ""),
            unidad=item.get("unidad", ""),
            cantidad=round(cantidad, 4),
            stock_minimo=round(minimo, 4),
            stock_maximo=round(maximo, 4),
            valor_estimado=round(valor, 4),
            estado=estado,
            ubicaciones=ubicaciones,
            lotes=len(lotes),
            movimientos=len(movimientos),
            dias_sin_movimiento=dias,
            motivos=motivos,
            datos={"familia": item.get("familia", "")},
        ).to_dict()
        return item_analizado, valor

    def _evaluar_estado_item(
        self,
        cantidad: float,
        minimo: float,
        maximo: float,
        ubicaciones: List[str],
        dias: int,
        dias_sin_movimiento: int,
        contadores: Dict[str, int],
    ) -> tuple[str, List[str]]:
        motivos: List[str] = []
        estado = "ok"

        if cantidad <= 0:
            estado = "sin_stock"
            motivos.append("Artículo sin stock disponible.")
            contadores["sin_stock"] += 1

        if minimo and cantidad < minimo:
            estado = "critico" if cantidad <= minimo * 0.25 else "stock_bajo"
            motivos.append(f"Stock por debajo del mínimo ({cantidad} < {minimo}).")
            contadores["stock_bajo"] += 1

        if minimo and cantidad <= minimo * 0.25:
            contadores["criticos"] += 1

        if maximo and cantidad > maximo:
            estado = "exceso_stock" if estado == "ok" else estado
            motivos.append(f"Stock por encima del máximo recomendado ({cantidad} > {maximo}).")
            contadores["exceso_stock"] += 1

        if not ubicaciones:
            motivos.append("Artículo sin ubicación registrada.")
            contadores["sin_ubicacion"] += 1

        if dias >= dias_sin_movimiento:
            motivos.append(f"Sin movimiento desde hace {dias} días.")
            contadores["sin_movimiento"] += 1
            if estado == "ok":
                estado = "sin_movimiento"

        return estado, motivos

    def _agrupar_movimientos(self, movimientos: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        movimientos_por_clave: Dict[str, List[Dict[str, Any]]] = {}
        for movimiento in movimientos:
            clave = movimiento.get("articulo_id") or movimiento.get("nombre", "").lower().strip()
            movimientos_por_clave.setdefault(clave, []).append(movimiento)
        return movimientos_por_clave

    def _extraer_ubicaciones(self, lotes: List[Dict[str, Any]]) -> List[str]:
        return sorted({(lote.get("ubicacion") or "").strip() for lote in lotes if (lote.get("ubicacion") or "").strip()})

    def _crear_contadores(self) -> Dict[str, int]:
        return {
            "sin_stock": 0,
            "stock_bajo": 0,
            "exceso_stock": 0,
            "criticos": 0,
            "sin_movimiento": 0,
            "sin_ubicacion": 0,
        }

    def _calcular_maximo(self, minimo: float, cantidad: float) -> float:
        if minimo > 0:
            return minimo * 3
        if cantidad > 0:
            return cantidad * 2
        return 0.0

    def _valorar_lotes(self, lotes: List[Dict[str, Any]]) -> float:
        return sum(
            float(lote.get("cantidad", 0) or 0) * float(lote.get("coste_unitario", 0) or 0)
            for lote in lotes
        )

    def _dias_desde_ultimo_movimiento(self, movimientos: List[Dict[str, Any]]) -> int:
        if not movimientos:
            return 999

        fechas = []
        for movimiento in movimientos:
            texto_fecha = movimiento.get("fecha") or movimiento.get("creado_en") or ""
            try:
                fechas.append(datetime.fromisoformat(texto_fecha).date())
            except Exception:
                pass

        if not fechas:
            return 999
        return max(0, (date.today() - max(fechas)).days)

    def _prioridad_estado(self, estado: str) -> int:
        return {
            "critico": 0,
            "sin_stock": 1,
            "stock_bajo": 2,
            "exceso_stock": 3,
            "sin_movimiento": 4,
            "ok": 9,
        }.get(estado, 8)
