from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json
import re

from MODELOS.validacion_ocr import ValidacionTextoOCR


class ValidadorCorrectorOCR:
    """
    Host AI 3.0.3.7.4

    Corrige errores típicos de OCR antes de pasar el texto al lector de facturas.
    No hace OCR real: limpia y normaliza texto extraído/manual.
    """

    REEMPLAZOS = {
        "F actura": "Factura",
        "Fact ura": "Factura",
        "T0TAL": "TOTAL",
        "TotaI": "Total",
        "lVA": "IVA",
        "lva": "IVA",
        " N0 ": " Nº ",
        " n0 ": " nº ",
        "O,": "0,",
    }

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def validar_y_corregir_texto(self, texto: str) -> Dict[str, Any]:
        original = texto or ""
        corregido = original
        correcciones = []
        avisos = []
        errores = []
        confianza = 100.0

        for mal, bien in self.REEMPLAZOS.items():
            if mal in corregido:
                corregido = corregido.replace(mal, bien)
                correcciones.append({"antes": mal, "despues": bien, "tipo": "reemplazo_simple"})

        # Normaliza saltos y espacios raros, pero mantiene líneas.
        lineas = []
        for linea in corregido.splitlines():
            limpia = " ".join(linea.replace("\t", " ").split())
            if limpia:
                lineas.append(limpia)
        corregido = "\n".join(lineas)

        if len(corregido.strip()) < 20:
            errores.append("Texto OCR demasiado corto.")
            confianza -= 50

        if not re.search(r"(factura|total|cif|iva|nº|num)", corregido, re.I):
            avisos.append("No se detectan palabras típicas de factura.")
            confianza -= 20

        # Corrige números OCR típicos: 8.45 -> 8,45 solo en importes si hay formato español mezclado.
        def normalizar_decimal(m):
            antes = m.group(0)
            despues = antes.replace(".", ",")
            correcciones.append({"antes": antes, "despues": despues, "tipo": "decimal"})
            return despues

        corregido = re.sub(r"\b\d{1,5}\.\d{2}\b", normalizar_decimal, corregido)

        valido = len(errores) == 0
        val = ValidacionTextoOCR(
            texto_original=original,
            texto_corregido=corregido,
            valido=valido,
            confianza=max(0.0, confianza),
            correcciones=correcciones,
            avisos=avisos,
            errores=errores,
        )
        datos = val.to_dict()
        datos["lectura_host_ai"] = "Texto OCR validado y corregido." if valido else "Texto OCR con errores."
        return datos

    def validar_resultado_ocr(self, resultado_ocr: Dict[str, Any]) -> Dict[str, Any]:
        datos = self.validar_y_corregir_texto(resultado_ocr.get("texto_extraido", ""))
        datos["resultado_ocr"] = resultado_ocr
        return datos

    def exportar_validacion(self, validacion: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "validacion_ocr.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(validacion, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Validación OCR exportada: {destino.name}."}
