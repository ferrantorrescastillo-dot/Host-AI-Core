from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json

from MODELOS.actualizacion_stock_factura import MovimientoStockFactura, InformeActualizacionStockFactura


class BaseActualizacionStockFactura:
    """
    Host AI 3.0.3.6.1

    Prepara movimientos de entrada de stock a partir de relaciones artículo-factura.
    Todavía no escribe en el motor de stock. Eso llega en 3.0.3.6.2.
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def preparar_movimiento(self, relacion: Dict[str, Any]) -> Dict[str, Any]:
        articulo_id = relacion.get("articulo_id", "")
        nombre = relacion.get("nombre_articulo", "") or relacion.get("descripcion_factura", "")
        cantidad = float(relacion.get("cantidad", 0) or 0)
        unidad = relacion.get("unidad", "") or "ud"

        avisos = []
        requiere_revision = False

        if not articulo_id:
            requiere_revision = True
            avisos.append("No hay artículo relacionado.")
        if cantidad <= 0:
            requiere_revision = True
            avisos.append("Cantidad inválida.")
        if not unidad:
            requiere_revision = True
            avisos.append("Falta unidad.")

        mov = MovimientoStockFactura(
            articulo_id=articulo_id,
            nombre_articulo=nombre,
            cantidad=cantidad,
            unidad=unidad,
            proveedor_id=relacion.get("proveedor_id", ""),
            proveedor_nombre=relacion.get("proveedor_nombre", ""),
            numero_factura=relacion.get("numero_factura", ""),
            fecha_factura=relacion.get("fecha_factura", ""),
            precio_unitario=float(relacion.get("precio_unitario", 0) or 0),
            importe=float(relacion.get("importe", 0) or 0),
            origen_linea=relacion,
            requiere_revision=requiere_revision,
            avisos=avisos,
        )
        datos = mov.to_dict()
        datos["lectura_host_ai"] = f"Movimiento preparado: {nombre} +{cantidad} {unidad}."
        return datos

    def preparar_informe(self, informe_relaciones: Dict[str, Any]) -> Dict[str, Any]:
        movimientos = []
        for rel in informe_relaciones.get("relaciones", []):
            d = self.preparar_movimiento(rel)
            movimientos.append(MovimientoStockFactura(
                articulo_id=d["articulo_id"],
                nombre_articulo=d["nombre_articulo"],
                cantidad=d["cantidad"],
                unidad=d["unidad"],
                proveedor_id=d["proveedor_id"],
                proveedor_nombre=d["proveedor_nombre"],
                numero_factura=d["numero_factura"],
                fecha_factura=d["fecha_factura"],
                precio_unitario=d["precio_unitario"],
                importe=d["importe"],
                origen_linea=d["origen_linea"],
                requiere_revision=d["requiere_revision"],
                avisos=d["avisos"],
            ))

        informe = InformeActualizacionStockFactura(movimientos=movimientos)
        datos = informe.to_dict()
        datos["lectura_host_ai"] = (
            f"Informe stock: {datos['entradas_preparadas']} entradas preparadas, "
            f"{datos['requieren_revision']} para revisar."
        )
        return datos

    def exportar_informe(self, informe: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "informe_actualizacion_stock_factura.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "archivo": str(destino),
            "lectura_host_ai": f"Informe stock exportado: {destino.name}.",
        }
