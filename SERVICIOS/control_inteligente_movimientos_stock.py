from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import json
from MODELOS.control_movimientos_stock_305 import LineaControlMovimientoStock, InformeControlMovimientosStock

class ControlInteligenteMovimientosStock:
    """Host AI 3.0.5.3 - Control Inteligente de Entradas y Salidas."""
    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.stock_dir = self.base_dir / "DATOS" / "stock"
        self.stock_dir.mkdir(parents=True, exist_ok=True)

    def analizar_movimientos(self) -> Dict[str, Any]:
        stock = getattr(self.core, "stock", None)
        movimientos_raw = stock.movimientos_listado() if stock else []
        movimientos: List[Dict[str, Any]] = []
        resumen_art: Dict[str, Any] = {}
        entradas = salidas = ajustes = mermas = descuadres = 0
        cant_entradas = cant_salidas = 0.0

        for m in movimientos_raw:
            tipo = (m.get("tipo") or "").lower().strip()
            motivo = (m.get("motivo") or "").lower().strip()
            cantidad = float(m.get("cantidad", 0) or 0)
            clave = m.get("articulo_id") or (m.get("nombre", "").lower().strip())
            observaciones: List[str] = []
            gravedad = "informativa"
            if tipo == "entrada":
                entradas += 1; cant_entradas += cantidad
            elif tipo == "salida":
                salidas += 1; cant_salidas += cantidad
            elif "ajuste" in tipo or "ajuste" in motivo:
                ajustes += 1
            if "merma" in motivo or "perdida" in motivo or "pérdida" in motivo:
                mermas += 1
            if cantidad <= 0:
                descuadres += 1; gravedad = "aviso"; observaciones.append("Movimiento con cantidad cero o negativa.")
            if tipo not in {"entrada", "salida", "ajuste"}:
                observaciones.append("Tipo de movimiento no normalizado.")
            if not m.get("unidad"):
                observaciones.append("Movimiento sin unidad.")
            if not m.get("nombre"):
                gravedad = "critica"; descuadres += 1; observaciones.append("Movimiento sin nombre de artículo.")

            resumen_art.setdefault(clave, {"nombre": m.get("nombre", clave), "articulo_id": m.get("articulo_id", ""), "unidad": m.get("unidad", ""), "entradas": 0.0, "salidas": 0.0, "movimientos": 0})
            resumen_art[clave]["movimientos"] += 1
            if tipo == "entrada": resumen_art[clave]["entradas"] += cantidad
            if tipo == "salida": resumen_art[clave]["salidas"] += cantidad

            movimientos.append(LineaControlMovimientoStock(
                tipo=tipo or "sin_tipo", nombre=m.get("nombre", ""), articulo_id=m.get("articulo_id", ""), unidad=m.get("unidad", ""),
                cantidad=round(cantidad, 4), motivo=m.get("motivo", ""), lote_id=m.get("lote_id", ""), fecha=m.get("fecha") or m.get("creado_en", ""),
                gravedad=gravedad, observaciones=observaciones).to_dict())

        for v in resumen_art.values():
            v["balance"] = round(float(v.get("entradas", 0)) - float(v.get("salidas", 0)), 4)
            v["entradas"] = round(float(v.get("entradas", 0)), 4)
            v["salidas"] = round(float(v.get("salidas", 0)), 4)

        resumen = {"estado": "revisar" if descuadres or mermas else "ok", "generado_en": datetime.now().isoformat(timespec="seconds")}
        lectura = f"Control inteligente de movimientos: {len(movimientos)} movimientos ({entradas} entradas, {salidas} salidas, {mermas} mermas, {descuadres} descuadres)."
        return InformeControlMovimientosStock(
            total_movimientos=len(movimientos), total_entradas=entradas, total_salidas=salidas, total_ajustes=ajustes, total_mermas=mermas, total_descuadres=descuadres,
            cantidad_entrada_total=round(cant_entradas, 4), cantidad_salida_total=round(cant_salidas, 4), movimientos=movimientos,
            resumen_por_articulo=resumen_art, resumen=resumen, lectura_host_ai=lectura).to_dict()

    def exportar_movimientos(self, informe: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        destino = self.stock_dir / (nombre or "control_inteligente_movimientos_stock.json")
        destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Control de entradas y salidas exportado: {destino.name}."}
