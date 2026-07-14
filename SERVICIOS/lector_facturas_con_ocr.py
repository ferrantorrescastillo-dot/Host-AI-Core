from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json


class LectorFacturasConOCR:
    """
    Host AI 3.0.3.7.3

    Integra OCR simulado con el lector completo de facturas:
    - Si el archivo necesita OCR, usa motor_ocr_simulado.
    - Con el texto OCR, reutiliza el lector completo de líneas.
    - Devuelve factura estructurada desde imagen/PDF escaneado.
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def leer_archivo_con_ocr(self, ruta_archivo: str, texto_manual: str = "", exportar_json: bool = True) -> Dict[str, Any]:
        ruta = Path(ruta_archivo)
        if not ruta.is_absolute():
            ruta = self.base_dir / ruta

        diagnostico = self.core.base_ocr_documentos.diagnosticar_archivo(str(ruta))

        if diagnostico.get("necesita_ocr"):
            ocr = self.core.motor_ocr_simulado.extraer_texto(str(ruta), texto_manual=texto_manual)
            texto = ocr.get("texto_extraido", "")
            validador_ocr = getattr(self.core, "validador_corrector_ocr", None)
            if validador_ocr is not None and texto:
                validacion_ocr = validador_ocr.validar_y_corregir_texto(texto)
                texto = validacion_ocr.get("texto_corregido", texto)
            else:
                validacion_ocr = None
            if not texto:
                datos = {
                    "ok": False,
                    "archivo": str(ruta),
                    "diagnostico": diagnostico,
                    "ocr": ocr,
                    "lectura_host_ai": "No se pudo leer factura escaneada: falta texto OCR.",
                    "errores": ["Falta texto OCR."],
                }
                return datos

            lectura = self.core.lector_completo_lineas_factura.leer_factura_texto_completa(
                texto=texto,
                proveedor_sugerido="",
                cif_sugerido="",
                numero_factura="",
                fecha_factura="",
                total_factura_detectado=0.0,
            )
            lectura["ok"] = True
            lectura["archivo"] = str(ruta)
            lectura["diagnostico_ocr"] = diagnostico
            lectura["resultado_ocr"] = ocr
            lectura["validacion_ocr"] = validacion_ocr
            lectura["origen"] = "ocr"
            lectura["lectura_host_ai"] = f"Factura leída mediante OCR: {lectura.get('total_lineas', 0)} líneas."
        else:
            lectura = self.core.lector_completo_lineas_factura.leer_factura_pdf_completa(
                ruta_archivo=str(ruta),
                exportar_json=exportar_json,
            )
            lectura["ok"] = True
            lectura["diagnostico_ocr"] = diagnostico
            lectura["origen"] = "pdf_texto"

        if exportar_json:
            exp = self.exportar_lectura(lectura)
            lectura["json_exportado_ocr"] = exp["archivo"]

        return lectura

    def validar_y_relacionar_archivo_ocr(self, ruta_archivo: str, texto_manual: str = "") -> Dict[str, Any]:
        lectura = self.leer_archivo_con_ocr(ruta_archivo, texto_manual=texto_manual, exportar_json=True)
        if not lectura.get("ok"):
            return lectura

        validacion_lineas = self.core.validador_lineas_factura.validar_factura_completa(lectura)
        relaciones = self.core.relacionador_automatico_articulos_factura.relacionar_bloque(lectura)
        validacion_relaciones = self.core.validador_relaciones_articulos_factura.validar_informe(relaciones)

        datos = {
            "ok": True,
            "lectura": lectura,
            "validacion_lineas": validacion_lineas,
            "relaciones": relaciones,
            "validacion_relaciones": validacion_relaciones,
            "lectura_host_ai": (
                f"Factura OCR procesada: {lectura.get('total_lineas', 0)} líneas, "
                f"{relaciones.get('relacionadas_auto', 0)} relaciones automáticas."
            ),
        }
        return datos

    def exportar_lectura(self, lectura: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "lectura_factura_con_ocr.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(lectura, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Lectura OCR factura exportada: {destino.name}."}
