from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
import json

from MODELOS.lineas_factura import LineaFactura, BloqueLineasFactura


class BaseLineasFactura:
    """
    Servicio base para trabajar con líneas de factura.

    En 3.0.3.3.1 todavía no parsea PDFs.
    Solo valida, serializa y exporta estructuras de líneas.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def crear_linea_demo(self) -> Dict[str, Any]:
        linea = LineaFactura(
            descripcion="Carrillera de ternera",
            cantidad=8,
            unidad="kg",
            precio_unitario=8.45,
            importe=67.60,
            confianza=99,
            origen_texto="Carrillera de ternera 8 KG 8,45 67,60",
        )
        return linea.to_dict()

    def crear_bloque_demo(self) -> Dict[str, Any]:
        bloque = BloqueLineasFactura(
            proveedor_id="PROV-MAKRO",
            proveedor_nombre="Makro",
            numero_factura="F-2026-001",
            fecha_factura="08/07/2026",
            total_factura_detectado=84.40,
            lineas=[
                LineaFactura("Carrillera de ternera", 8, "kg", 8.45, 67.60, confianza=99),
                LineaFactura("Cebolla", 15, "kg", 1.12, 16.80, confianza=98),
            ],
        )
        return bloque.to_dict()

    def validar_bloque(self, bloque: Dict[str, Any]) -> Dict[str, Any]:
        errores = []
        for i, linea in enumerate(bloque.get("lineas", []), start=1):
            if not linea.get("descripcion"):
                errores.append(f"Línea {i}: falta descripción.")
            if float(linea.get("cantidad", 0) or 0) <= 0:
                errores.append(f"Línea {i}: cantidad inválida.")
            if not linea.get("unidad"):
                errores.append(f"Línea {i}: falta unidad.")
            if float(linea.get("importe", 0) or 0) <= 0:
                errores.append(f"Línea {i}: importe inválido.")
        return {
            "ok": len(errores) == 0,
            "errores": errores,
            "total_errores": len(errores),
            "lectura_host_ai": "Bloque de líneas válido." if not errores else f"Bloque con {len(errores)} errores.",
        }

    def exportar_bloque(self, bloque: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "bloque_lineas_factura.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(bloque, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "archivo": str(destino),
            "lectura_host_ai": f"Bloque de líneas exportado: {destino.name}.",
        }
