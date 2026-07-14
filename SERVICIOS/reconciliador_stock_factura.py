from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import json

from MODELOS.reconciliacion_stock_factura import ResultadoReconciliacionStock, InformeReconciliacionStock


class ReconciliadorStockFactura:
    """
    Host AI 3.0.3.6.5

    Comprueba si las entradas de stock aplicadas coinciden con lo que decía la factura.
    Sirve para cerrar el circuito:
    factura leída -> líneas -> artículos -> stock aplicado -> conciliación.
    """

    TOLERANCIA = 0.0001

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def reconciliar_movimiento(self, movimiento: Dict[str, Any]) -> Dict[str, Any]:
        articulo_id = movimiento.get("articulo_id", "")
        nombre = movimiento.get("nombre_articulo", "")
        cantidad_factura = float(movimiento.get("cantidad", 0) or 0)
        unidad = movimiento.get("unidad", "")

        hist = getattr(self.core, "historico_inteligente_stock", None)
        cantidad_aplicada = 0.0
        avisos = []

        if hist:
            for r in hist.registros:
                if r.articulo_id == articulo_id and r.tipo == "entrada":
                    if movimiento.get("numero_factura") and r.numero_factura and r.numero_factura != movimiento.get("numero_factura"):
                        continue
                    cantidad_aplicada += float(r.cantidad or 0)
        else:
            avisos.append("No existe histórico de stock.")

        diferencia = round(cantidad_factura - cantidad_aplicada, 4)
        if not articulo_id:
            estado = "pendiente"
            avisos.append("Movimiento sin artículo.")
        elif abs(diferencia) <= self.TOLERANCIA or cantidad_aplicada >= cantidad_factura:
            estado = "correcto"
        elif cantidad_aplicada == 0:
            estado = "pendiente"
            avisos.append("No consta entrada aplicada para este artículo.")
        else:
            estado = "diferencia"
            avisos.append("La cantidad aplicada no coincide con la factura.")

        res = ResultadoReconciliacionStock(
            articulo_id=articulo_id,
            nombre_articulo=nombre,
            cantidad_factura=cantidad_factura,
            cantidad_aplicada=round(cantidad_aplicada, 4),
            unidad=unidad,
            diferencia=diferencia,
            estado=estado,
            avisos=avisos,
            datos=movimiento,
        )
        datos = res.to_dict()
        datos["lectura_host_ai"] = f"Reconciliación {nombre}: {estado}."
        return datos

    def reconciliar_informe(self, informe_stock: Dict[str, Any]) -> Dict[str, Any]:
        resultados = []
        for mov in informe_stock.get("movimientos", []):
            d = self.reconciliar_movimiento(mov)
            resultados.append(ResultadoReconciliacionStock(
                articulo_id=d["articulo_id"],
                nombre_articulo=d["nombre_articulo"],
                cantidad_factura=d["cantidad_factura"],
                cantidad_aplicada=d["cantidad_aplicada"],
                unidad=d["unidad"],
                diferencia=d["diferencia"],
                estado=d["estado"],
                avisos=d["avisos"],
                datos=d["datos"],
            ))

        informe = InformeReconciliacionStock(resultados=resultados)
        datos = informe.to_dict()
        datos["lectura_host_ai"] = (
            f"Reconciliación stock: {datos['correctos']} correctos, "
            f"{datos['con_diferencias']} diferencias, {datos['pendientes']} pendientes."
        )
        return datos

    def exportar_informe(self, informe: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "reconciliacion_stock_factura.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Reconciliación stock exportada: {destino.name}."}
