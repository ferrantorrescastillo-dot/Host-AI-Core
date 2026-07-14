from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json

from MODELOS.ocr_documentos import DiagnosticoOCRDocumento


class BaseOCRDocumentos:
    """
    Host AI 3.0.3.7.1

    Base para detectar documentos que necesitan OCR.
    Importante:
    - Esta versión NO hace OCR real todavía.
    - Diagnostica PDFs/imágenes escaneadas.
    - Deja preparado el flujo para 3.0.3.7.2.
    """

    MIN_CARACTERES_PDF_TEXTO = 40

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def diagnosticar_archivo(self, ruta_archivo: str) -> Dict[str, Any]:
        ruta = Path(ruta_archivo)
        if not ruta.is_absolute():
            ruta = self.base_dir / ruta

        if not ruta.exists():
            raise FileNotFoundError(f"No existe el archivo: {ruta}")

        ext = ruta.suffix.lower()
        if ext == ".pdf":
            return self._diagnosticar_pdf(ruta)
        if ext in [".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"]:
            return self._diagnosticar_imagen(ruta)

        diag = DiagnosticoOCRDocumento(
            archivo=str(ruta),
            nombre_archivo=ruta.name,
            necesita_ocr=False,
            motivo="Tipo de archivo no preparado para OCR.",
            recomendaciones=["Usar PDF o imagen."],
            confianza=0,
        )
        datos = diag.to_dict()
        datos["lectura_host_ai"] = "Archivo no compatible con OCR."
        return datos

    def _diagnosticar_pdf(self, ruta: Path) -> Dict[str, Any]:
        try:
            analisis = self.core.lector_pdf_facturas.analizar_pdf(str(ruta), exportar_json=False)
            caracteres = int(analisis.get("total_caracteres", 0) or 0)
            paginas = int(analisis.get("total_paginas", 0) or 0)
            necesita = caracteres < self.MIN_CARACTERES_PDF_TEXTO
            motivo = "PDF con poco texto extraíble; probablemente escaneado." if necesita else "PDF con texto extraíble suficiente."
            recomendaciones = []
            if necesita:
                recomendaciones.append("Enviar a motor OCR en 3.0.3.7.2.")
                recomendaciones.append("Si es factura, revisar calidad del escaneo.")
            else:
                recomendaciones.append("Usar lector PDF normal.")

            diag = DiagnosticoOCRDocumento(
                archivo=str(ruta),
                nombre_archivo=ruta.name,
                necesita_ocr=necesita,
                motivo=motivo,
                texto_actual=(analisis.get("texto_completo", "") or "")[:1000],
                caracteres_detectados=caracteres,
                paginas=paginas,
                confianza=90 if necesita else 95,
                recomendaciones=recomendaciones,
            )
        except Exception as exc:
            diag = DiagnosticoOCRDocumento(
                archivo=str(ruta),
                nombre_archivo=ruta.name,
                necesita_ocr=True,
                motivo=f"No se pudo extraer texto del PDF: {exc}",
                confianza=80,
                recomendaciones=["Enviar a motor OCR."],
            )

        datos = diag.to_dict()
        datos["lectura_host_ai"] = "Documento necesita OCR." if datos["necesita_ocr"] else "Documento no necesita OCR."
        return datos

    def _diagnosticar_imagen(self, ruta: Path) -> Dict[str, Any]:
        diag = DiagnosticoOCRDocumento(
            archivo=str(ruta),
            nombre_archivo=ruta.name,
            necesita_ocr=True,
            motivo="Es una imagen; necesita OCR para extraer texto.",
            caracteres_detectados=0,
            paginas=1,
            confianza=95,
            recomendaciones=["Enviar a motor OCR en 3.0.3.7.2."],
        )
        datos = diag.to_dict()
        datos["lectura_host_ai"] = "Imagen detectada: necesita OCR."
        return datos

    def diagnosticar_lote(self, rutas: list[str]) -> Dict[str, Any]:
        resultados = [self.diagnosticar_archivo(r) for r in rutas]
        return {
            "resultados": resultados,
            "total": len(resultados),
            "necesitan_ocr": sum(1 for r in resultados if r.get("necesita_ocr")),
            "lectura_host_ai": f"Diagnóstico OCR: {sum(1 for r in resultados if r.get('necesita_ocr'))} de {len(resultados)} necesitan OCR.",
        }

    def exportar_diagnostico(self, diagnostico: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "diagnostico_ocr_documentos.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(diagnostico, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Diagnóstico OCR exportado: {destino.name}."}
