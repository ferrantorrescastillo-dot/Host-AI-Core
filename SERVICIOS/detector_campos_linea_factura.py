from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
import re
import json


class DetectorCamposLineaFactura:
    """
    Host AI 3.0.3.3.3

    Detector especializado de campos dentro de una línea de factura:
    - cantidad
    - unidad
    - precio unitario
    - importe
    - descripción
    - confianza
    """

    UNIDADES = {
        "kg": "kg", "kgs": "kg", "kilo": "kg", "kilos": "kg",
        "g": "g", "gr": "g", "gramos": "g",
        "l": "L", "lt": "L", "litro": "L", "litros": "L",
        "ml": "ml",
        "ud": "ud", "uds": "ud", "u": "ud", "unidad": "ud", "unidades": "ud",
        "caja": "caja", "cajas": "caja",
        "paq": "paq", "pack": "pack",
        "bote": "bote", "bot": "bote",
    }

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def detectar_campos(self, linea_texto: str) -> Dict[str, Any]:
        texto = " ".join(str(linea_texto or "").strip().split())
        if not texto:
            return self._vacio(linea_texto, "línea vacía")

        importes = self._extraer_importes(texto)
        if len(importes) < 2:
            return self._vacio(linea_texto, "no hay suficientes importes")

        precio_unitario = importes[-2]["valor"]
        importe = importes[-1]["valor"]
        texto_sin_importes = self._quitar_spans(texto, [importes[-2]["span"], importes[-1]["span"]])

        cantidad_info = self._extraer_cantidad_unidad(texto_sin_importes)
        if not cantidad_info:
            return self._vacio(linea_texto, "no se detecta cantidad/unidad")

        cantidad = cantidad_info["cantidad"]
        unidad = cantidad_info["unidad"]
        span = cantidad_info["span"]

        descripcion = (texto_sin_importes[:span[0]] + " " + texto_sin_importes[span[1]:]).strip()
        descripcion = self._limpiar_descripcion(descripcion)

        esperado = round(cantidad * precio_unitario, 2)
        diferencia = round(importe - esperado, 2)
        confianza = 100.0
        avisos = []

        if not descripcion:
            confianza -= 30
            avisos.append("Descripción vacía.")
        if abs(diferencia) > 0.05:
            confianza -= 20
            avisos.append(f"Importe no cuadra: {cantidad} x {precio_unitario} = {esperado}, importe {importe}.")
        if precio_unitario <= 0 or importe <= 0:
            confianza -= 20
            avisos.append("Precio o importe inválido.")
        if cantidad <= 0:
            confianza -= 20
            avisos.append("Cantidad inválida.")

        return {
            "ok": True,
            "descripcion": descripcion,
            "cantidad": cantidad,
            "unidad": unidad,
            "precio_unitario": precio_unitario,
            "importe": importe,
            "importe_calculado": esperado,
            "diferencia": diferencia,
            "confianza": max(0.0, confianza),
            "avisos": avisos,
            "origen_texto": linea_texto,
            "lectura_host_ai": f"Línea detectada: {descripcion} | {cantidad} {unidad} | {precio_unitario} | {importe}",
        }

    def detectar_lote(self, lineas: List[str]) -> Dict[str, Any]:
        resultados = [self.detectar_campos(l) for l in lineas]
        ok = [r for r in resultados if r.get("ok")]
        return {
            "lineas": resultados,
            "total": len(resultados),
            "detectadas": len(ok),
            "confianza_media": round(sum(r.get("confianza", 0) for r in ok) / len(ok), 2) if ok else 0.0,
            "lectura_host_ai": f"Campos detectados en {len(ok)} de {len(resultados)} líneas.",
        }

    def exportar_resultados(self, resultados: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "deteccion_campos_linea_factura.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "archivo": str(destino),
            "lectura_host_ai": f"Detección de campos exportada: {destino.name}.",
        }

    def _extraer_importes(self, texto: str) -> List[Dict[str, Any]]:
        out = []
        for m in re.finditer(r"(?<![A-Za-z])(\d{1,6}(?:[.,]\d{2}))(?![A-Za-z])", texto):
            try:
                out.append({"valor": float(m.group(1).replace(",", ".")), "span": m.span(), "texto": m.group(1)})
            except Exception:
                pass
        return out

    def _extraer_cantidad_unidad(self, texto: str):
        # Última cantidad+unidad para evitar confundir "Aceite 5L 2 UD"
        patrones = [
            r"\b(\d+(?:[.,]\d+)?)\s*(kg|kgs|g|gr|l|lt|ml|ud|uds|u|unidad|unidades|caja|cajas|paq|pack|bote|bot)\b",
            r"\b(\d+(?:[.,]\d+)?)(kg|kgs|g|gr|l|lt|ml|ud|uds|u)\b",
        ]
        matches = []
        for patron in patrones:
            matches = list(re.finditer(patron, texto, re.I))
            if matches:
                break
        if not matches:
            return None
        m = matches[-1]
        return {
            "cantidad": float(m.group(1).replace(",", ".")),
            "unidad": self._normalizar_unidad(m.group(2)),
            "span": m.span(),
        }

    def _normalizar_unidad(self, unidad: str) -> str:
        return self.UNIDADES.get(str(unidad).lower().strip(), str(unidad).lower().strip())

    def _quitar_spans(self, texto: str, spans):
        nuevo = texto
        for start, end in sorted(spans, reverse=True):
            nuevo = nuevo[:start] + nuevo[end:]
        return " ".join(nuevo.split())

    def _limpiar_descripcion(self, descripcion: str) -> str:
        descripcion = re.sub(r"\b(cod|ref|sku)\.?\s*[A-Z0-9\-]+\b", "", descripcion, flags=re.I)
        return " ".join(descripcion.strip(" -").split())

    def _vacio(self, texto, motivo):
        return {
            "ok": False,
            "descripcion": "",
            "cantidad": 0.0,
            "unidad": "",
            "precio_unitario": 0.0,
            "importe": 0.0,
            "confianza": 0.0,
            "avisos": [motivo],
            "origen_texto": texto,
            "lectura_host_ai": f"No se pudo detectar línea: {motivo}.",
        }
