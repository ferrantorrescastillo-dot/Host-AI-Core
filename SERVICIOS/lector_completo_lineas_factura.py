from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
import json


class LectorCompletoLineasFactura:
    """
    Host AI 3.0.3.3.4

    Integra:
    - lector PDF
    - detector proveedor
    - parser de líneas
    - exportación del bloque completo

    Esta versión NO relaciona todavía las líneas con artículos internos.
    Eso vendrá en 3.0.3.4.
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def leer_factura_pdf_completa(self, ruta_archivo: str, exportar_json: bool = True) -> Dict[str, Any]:
        analisis_pdf = self.core.lector_pdf_facturas.analizar_pdf(ruta_archivo, exportar_json=True)
        det_factura = analisis_pdf.get("deteccion_factura", {})

        det_proveedor = self.core.detector_proveedores_pdf.detectar_desde_texto(
            texto=analisis_pdf.get("texto_completo", ""),
            proveedor_sugerido=det_factura.get("proveedor", ""),
            cif_sugerido=det_factura.get("cif", ""),
            contexto={"archivo": analisis_pdf.get("archivo")},
        )

        bloque = self.core.parser_lineas_factura.leer_lineas_desde_texto(
            texto=analisis_pdf.get("texto_completo", ""),
            proveedor_id=det_proveedor.get("proveedor_id", ""),
            proveedor_nombre=det_proveedor.get("nombre", det_factura.get("proveedor", "")),
            numero_factura=det_factura.get("numero_factura", ""),
            fecha_factura=det_factura.get("fecha", ""),
            total_factura_detectado=det_factura.get("total", 0.0),
        )
        bloque["archivo"] = analisis_pdf.get("archivo", "")
        bloque["deteccion_factura"] = det_factura
        bloque["deteccion_proveedor"] = det_proveedor

        avisos = list(bloque.get("avisos", []))
        if not det_proveedor.get("proveedor_id"):
            avisos.append("Proveedor no reconocido en diccionario.")
        if bloque.get("total_lineas", 0) == 0:
            avisos.append("No se han detectado líneas de producto.")
        if bloque.get("diferencia_total", 0) and abs(float(bloque.get("diferencia_total", 0))) > 0.10:
            avisos.append("La suma de líneas no coincide con el total factura. Puede ser por IVA, descuentos o portes.")
        bloque["avisos"] = avisos

        if exportar_json:
            exportado = self.exportar_lectura(bloque)
            bloque["json_exportado"] = exportado["archivo"]

        bloque["lectura_host_ai"] = (
            f"Factura PDF leída: {bloque.get('total_lineas', 0)} líneas, "
            f"proveedor {det_proveedor.get('nombre') or 'pendiente'}, "
            f"factura {det_factura.get('numero_factura') or 'sin número'}."
        )
        return bloque

    def leer_factura_texto_completa(
        self,
        texto: str,
        proveedor_sugerido: str = "",
        cif_sugerido: str = "",
        numero_factura: str = "",
        fecha_factura: str = "",
        total_factura_detectado: float = 0.0,
    ) -> Dict[str, Any]:
        det_proveedor = self.core.detector_proveedores_pdf.detectar_desde_texto(
            texto=texto,
            proveedor_sugerido=proveedor_sugerido,
            cif_sugerido=cif_sugerido,
        )

        bloque = self.core.parser_lineas_factura.leer_lineas_desde_texto(
            texto=texto,
            proveedor_id=det_proveedor.get("proveedor_id", ""),
            proveedor_nombre=det_proveedor.get("nombre", proveedor_sugerido),
            numero_factura=numero_factura,
            fecha_factura=fecha_factura,
            total_factura_detectado=total_factura_detectado,
        )
        bloque["deteccion_proveedor"] = det_proveedor
        bloque["lectura_host_ai"] = (
            f"Texto factura leído: {bloque.get('total_lineas', 0)} líneas, "
            f"proveedor {det_proveedor.get('nombre') or 'pendiente'}."
        )
        return bloque

    def exportar_lectura(self, lectura: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "lectura_completa_lineas_factura.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(lectura, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "archivo": str(destino),
            "lectura_host_ai": f"Lectura completa de factura exportada: {destino.name}.",
        }
