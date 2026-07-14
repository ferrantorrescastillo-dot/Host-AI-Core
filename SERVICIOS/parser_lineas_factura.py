from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any
import re
import json

from MODELOS.lineas_factura import LineaFactura, BloqueLineasFactura


class ParserLineasFactura:
    UNIDADES = {
        "kg": "kg", "kgs": "kg", "kilo": "kg", "kilos": "kg",
        "g": "g", "gr": "g", "gramos": "g",
        "l": "L", "lt": "L", "litro": "L", "litros": "L",
        "ml": "ml",
        "ud": "ud", "uds": "ud", "unidad": "ud", "unidades": "ud",
        "caja": "caja", "cajas": "caja",
    }

    PALABRAS_DESCARTAR = [
        "total", "base imponible", "iva", "i.v.a", "factura", "fecha",
        "cif", "subtotal", "importe total", "albaran", "albarán",
    ]

    def __init__(self, base_dir: Path, detector_campos_linea=None):
        self.base_dir = Path(base_dir)
        self.detector_campos_linea = detector_campos_linea
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def leer_lineas_desde_texto(
        self,
        texto: str,
        proveedor_id: str = "",
        proveedor_nombre: str = "",
        numero_factura: str = "",
        fecha_factura: str = "",
        total_factura_detectado: float = 0.0,
    ) -> Dict[str, Any]:
        lineas = []
        descartadas = []

        for idx, raw in enumerate((texto or "").splitlines(), start=1):
            raw = raw.strip()
            if not raw:
                continue
            if self._descartar_linea(raw):
                descartadas.append({"numero": idx, "texto": raw, "motivo": "cabecera_pie"})
                continue

            linea = self._parsear_linea(raw)
            if linea:
                linea.proveedor_id = proveedor_id
                linea.numero_factura = numero_factura
                linea.fecha_factura = fecha_factura
                lineas.append(linea)
            else:
                descartadas.append({"numero": idx, "texto": raw, "motivo": "no_parseable"})

        bloque = BloqueLineasFactura(
            proveedor_id=proveedor_id,
            proveedor_nombre=proveedor_nombre,
            numero_factura=numero_factura,
            fecha_factura=fecha_factura,
            total_factura_detectado=total_factura_detectado,
            lineas=lineas,
            lineas_descartadas=descartadas,
        )
        datos = bloque.to_dict()
        datos["lectura_host_ai"] = f"Líneas de factura leídas: {datos['total_lineas']} líneas estructuradas."
        return datos

    def leer_lineas_desde_pdf(self, ruta_archivo: str, lector_pdf_facturas, detector_proveedores_pdf=None) -> Dict[str, Any]:
        analisis = lector_pdf_facturas.analizar_pdf(ruta_archivo, exportar_json=True)
        det_fact = analisis.get("deteccion_factura", {})
        proveedor_id = ""
        proveedor_nombre = det_fact.get("proveedor", "")
        if detector_proveedores_pdf:
            det_prov = detector_proveedores_pdf.detectar_desde_texto(
                texto=analisis.get("texto_completo", ""),
                proveedor_sugerido=det_fact.get("proveedor", ""),
                cif_sugerido=det_fact.get("cif", ""),
            )
            proveedor_id = det_prov.get("proveedor_id", "")
            proveedor_nombre = det_prov.get("nombre", proveedor_nombre)

        datos = self.leer_lineas_desde_texto(
            texto=analisis.get("texto_completo", ""),
            proveedor_id=proveedor_id,
            proveedor_nombre=proveedor_nombre,
            numero_factura=det_fact.get("numero_factura", ""),
            fecha_factura=det_fact.get("fecha", ""),
            total_factura_detectado=det_fact.get("total", 0.0),
        )
        datos["archivo"] = analisis.get("archivo", "")
        return datos

    def exportar_lineas(self, bloque: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "lineas_factura.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(bloque, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Líneas de factura exportadas: {destino.name}."}

    def _parsear_linea(self, texto: str) -> LineaFactura | None:
        if self.detector_campos_linea is not None:
            r = self.detector_campos_linea.detectar_campos(texto)
            if r.get("ok"):
                return LineaFactura(
                    descripcion=r["descripcion"],
                    cantidad=r["cantidad"],
                    unidad=r["unidad"],
                    precio_unitario=r["precio_unitario"],
                    importe=r["importe"],
                    confianza=r["confianza"],
                    origen_texto=texto,
                    avisos=r.get("avisos", []),
                )

        importes = self._extraer_importes(texto)
        if len(importes) < 2:
            return None

        precio_unitario = importes[-2]
        importe = importes[-1]
        texto_sin_importes = self._quitar_ultimos_importes(texto, 2)

        cantidad, unidad, span = self._extraer_cantidad_unidad(texto_sin_importes)
        if cantidad <= 0 or not unidad:
            return None

        descripcion = (texto_sin_importes[:span[0]] + " " + texto_sin_importes[span[1]:]).strip()
        descripcion = self._limpiar_descripcion(" ".join(descripcion.split()))
        if not descripcion:
            return None

        confianza = self._calcular_confianza(descripcion, cantidad, unidad, precio_unitario, importe)
        avisos = []
        esperado = round(cantidad * precio_unitario, 2)
        if abs(esperado - importe) > 0.05:
            avisos.append(f"Importe no cuadra exactamente: {cantidad} x {precio_unitario} = {esperado}, factura {importe}.")
            confianza -= 15

        return LineaFactura(
            descripcion=descripcion,
            cantidad=cantidad,
            unidad=unidad,
            precio_unitario=precio_unitario,
            importe=importe,
            confianza=max(0, confianza),
            origen_texto=texto,
            avisos=avisos,
        )

    def _descartar_linea(self, texto: str) -> bool:
        t = texto.lower()
        # Descarta líneas claramente de cabecera/pie, pero no productos con palabras parecidas.
        if any(p in t for p in ["base imponible", "total factura", "importe total", "subtotal"]):
            return True
        if t in {"factura", "iva", "i.v.a"}:
            return True
        if t.startswith("factura ") or t.startswith("fecha ") or t.startswith("cif "):
            return True
        # Línea de IVA típica: IVA 16,42
        if re.match(r"^i\.?v\.?a\.?\s+\d", t):
            return True
        return False

    def _extraer_importes(self, texto: str) -> List[float]:
        vals = []
        # Permite 8,45 / 67,60 / 39.90
        for m in re.finditer(r"(?<![A-Za-z])(\d{1,6}(?:[.,]\d{2}))(?![A-Za-z])", texto):
            try:
                vals.append(float(m.group(1).replace(",", ".")))
            except Exception:
                pass
        return vals

    def _quitar_ultimos_importes(self, texto: str, cantidad: int) -> str:
        matches = list(re.finditer(r"(?<![A-Za-z])(\d{1,6}(?:[.,]\d{2}))(?![A-Za-z])", texto))
        quitar = matches[-cantidad:] if len(matches) >= cantidad else []
        nuevo = texto
        for m in reversed(quitar):
            nuevo = nuevo[:m.start()] + nuevo[m.end():]
        return " ".join(nuevo.split())

    def _extraer_cantidad_unidad(self, texto: str):
        # Elegimos la última cantidad+unidad de la línea para no confundir "Aceite 5L 2 UD":
        # producto contiene 5L, cantidad real es 2 UD.
        matches = list(re.finditer(r"\b(\d+(?:[.,]\d+)?)\s*(kg|kgs|g|gr|l|lt|ml|ud|uds|unidad|unidades|caja|cajas)\b", texto, re.I))
        if not matches:
            matches = list(re.finditer(r"\b(\d+(?:[.,]\d+)?)(kg|kgs|g|gr|l|lt|ml|ud|uds)\b", texto, re.I))
        if matches:
            m = matches[-1]
            return float(m.group(1).replace(",", ".")), self._normalizar_unidad(m.group(2)), m.span()
        return 0.0, "", (0, 0)

    def _normalizar_unidad(self, unidad: str) -> str:
        return self.UNIDADES.get(str(unidad).lower().strip(), str(unidad).lower().strip())

    def _limpiar_descripcion(self, descripcion: str) -> str:
        descripcion = re.sub(r"\b(cod|ref|sku)\.?\s*[A-Z0-9\-]+\b", "", descripcion, flags=re.I)
        return " ".join(descripcion.strip(" -").split())

    def _calcular_confianza(self, descripcion: str, cantidad: float, unidad: str, precio: float, importe: float) -> float:
        puntos = 0
        if descripcion: puntos += 30
        if cantidad > 0: puntos += 20
        if unidad: puntos += 20
        if precio > 0: puntos += 15
        if importe > 0: puntos += 15
        return float(puntos)
