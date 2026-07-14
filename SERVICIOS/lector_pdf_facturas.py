from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import json
import re

from MODELOS.pdf_facturas import AnalisisPDF, PaginaPDF, DeteccionFacturaPDF


class LectorPDFFacturas:
    """
    Host AI 3.0.3.1 - Lector Universal PDF / Facturas.

    Primera fase PDF:
    - Lee PDFs con texto embebido.
    - Extrae texto por página.
    - Detecta datos básicos de factura.
    - Exporta análisis JSON.
    - No hace OCR todavía.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def analizar_pdf(self, ruta_archivo: str, exportar_json: bool = True) -> Dict[str, Any]:
        ruta = Path(ruta_archivo)
        if not ruta.is_absolute():
            ruta = self.base_dir / ruta

        if not ruta.exists():
            raise FileNotFoundError(f"No existe el PDF: {ruta}")

        if ruta.suffix.lower() != ".pdf":
            raise ValueError("Solo se soportan archivos .pdf en este lector.")

        paginas, metodo = self._extraer_texto_pdf(ruta)
        texto_completo = "\n".join(p.texto for p in paginas).strip()

        analisis = AnalisisPDF(
            archivo=str(ruta),
            nombre_archivo=ruta.name,
            paginas=paginas,
            texto_completo=texto_completo,
            total_paginas=len(paginas),
            total_caracteres=len(texto_completo),
            metodo_extraccion=metodo,
        )
        datos = analisis.to_dict()

        deteccion = self.detectar_factura_desde_texto(texto_completo)
        datos["deteccion_factura"] = deteccion

        if exportar_json:
            exportado = self.exportar_analisis_json(datos)
            datos["json_exportado"] = exportado["archivo"]

        datos["lectura_host_ai"] = (
            f"PDF analizado: {ruta.name}. {datos['total_paginas']} páginas, "
            f"{datos['total_caracteres']} caracteres. Proveedor detectado: "
            f"{deteccion.get('proveedor') or 'pendiente'}."
        )
        return datos

    def detectar_factura_desde_texto(self, texto: str) -> Dict[str, Any]:
        limpio = texto or ""
        lineas = [l.strip() for l in limpio.splitlines() if l.strip()]
        avisos = []

        proveedor = self._detectar_proveedor(lineas)
        cif = self._buscar_patron(limpio, r"\b([A-Z][0-9]{8}|[A-Z0-9]{8,10})\b", "")
        numero = self._detectar_numero_factura(limpio)
        fecha = self._buscar_patron(
            limpio,
            r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b",
            "",
        )

        total = self._buscar_importe_total(limpio, ["total factura", "total", "importe total"])
        base = self._buscar_importe_total(limpio, ["base imponible", "base"])
        iva = self._buscar_importe_total(limpio, ["iva", "i.v.a"])

        puntos = 0
        if proveedor:
            puntos += 25
        else:
            avisos.append("No se ha detectado proveedor claro.")
        if numero:
            puntos += 20
        else:
            avisos.append("No se ha detectado número de factura.")
        if fecha:
            puntos += 15
        else:
            avisos.append("No se ha detectado fecha.")
        if total:
            puntos += 30
        else:
            avisos.append("No se ha detectado total.")
        if base or iva:
            puntos += 10

        return DeteccionFacturaPDF(
            proveedor=proveedor,
            cif=cif,
            numero_factura=numero,
            fecha=fecha,
            total=total,
            base_imponible=base,
            iva=iva,
            confianza=float(min(100, puntos)),
            avisos=avisos,
        ).to_dict()

    def exportar_analisis_json(self, analisis: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or f"analisis_pdf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(analisis, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return {
            "archivo": str(destino),
            "lectura_host_ai": f"Análisis PDF exportado: {destino.name}.",
        }

    def _extraer_texto_pdf(self, ruta: Path) -> tuple[List[PaginaPDF], str]:
        # Preferimos PyPDF2/pypdf si están disponibles.
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(ruta))
            paginas = []
            for i, page in enumerate(reader.pages, start=1):
                texto = page.extract_text() or ""
                paginas.append(PaginaPDF(numero=i, texto=texto, caracteres=len(texto)))
            return paginas, "PyPDF2"
        except Exception:
            pass

        try:
            from pypdf import PdfReader
            reader = PdfReader(str(ruta))
            paginas = []
            for i, page in enumerate(reader.pages, start=1):
                texto = page.extract_text() or ""
                paginas.append(PaginaPDF(numero=i, texto=texto, caracteres=len(texto)))
            return paginas, "pypdf"
        except Exception as exc:
            raise RuntimeError(
                "No se pudo leer el PDF. Instala PyPDF2 o pypdf. "
                "Este sprint no usa OCR todavía."
            ) from exc

    def _detectar_numero_factura(self, texto: str) -> str:
        patrones = [
            r"factura\s*(?:n[ºo]\.?|numero|número)?\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-\/]+)",
            r"(?:n[ºo]\.?|numero|número)\s*(?:factura)?\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-\/]+)",
            r"\b(F[\-\/]?\d{2,}[A-Z0-9\-\/]*)\b",
        ]
        for patron in patrones:
            m = re.search(patron, texto, re.IGNORECASE)
            if m:
                valor = str(m.group(1)).strip()
                if valor.lower() not in {"factura", "numero", "n"}:
                    return valor
        return ""

    def _detectar_proveedor(self, lineas: List[str]) -> str:
        if not lineas:
            return ""
        # Evita líneas genéricas si puede.
        genericas = {"factura", "invoice", "albaran", "albarán"}
        for linea in lineas[:8]:
            l = linea.strip()
            if not l:
                continue
            if l.lower() in genericas:
                continue
            if any(k in l.lower() for k in ["factura", "fecha", "nº", "numero", "número", "total"]):
                continue
            return l[:80]
        return lineas[0][:80]

    def _buscar_patron(self, texto: str, patron: str, default: str = "", flags: int = 0) -> str:
        m = re.search(patron, texto, flags)
        if not m:
            return default
        return str(m.group(1)).strip()

    def _buscar_importe_total(self, texto: str, claves: List[str]) -> float:
        # Busca importes cerca de palabras clave.
        lineas = texto.splitlines()
        for linea in lineas:
            normal = linea.lower()
            if any(c in normal for c in claves):
                importe = self._ultimo_importe(linea)
                if importe:
                    return importe

        # Fallback: último importe del documento.
        importes = []
        for m in re.finditer(r"(\d{1,6}(?:[.,]\d{2}))\s*€?", texto):
            try:
                importes.append(float(m.group(1).replace(",", ".")))
            except Exception:
                pass
        return importes[-1] if importes else 0.0

    def _ultimo_importe(self, texto: str) -> float:
        importes = []
        for m in re.finditer(r"(\d{1,6}(?:[.,]\d{2}))\s*€?", texto):
            try:
                importes.append(float(m.group(1).replace(",", ".")))
            except Exception:
                pass
        return importes[-1] if importes else 0.0
