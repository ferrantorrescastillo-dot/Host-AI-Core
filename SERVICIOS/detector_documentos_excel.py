from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any
import unicodedata

from MODELOS.deteccion_excel import (
    TipoDocumentoDetectado,
    DeteccionHojaExcel,
    DeteccionDocumentoExcel,
)


class DetectorDocumentosExcel:
    """
    Detector Inteligente de Documentos Excel v3.0.2.2.

    Usa el análisis del lector Excel para detectar si cada hoja parece:
    - escandallo
    - listado_articulos
    - inventario
    - compras
    - produccion
    - proveedores
    - desconocido

    Es determinista y explicable: devuelve confianza y motivos.
    """

    REGLAS = {
        "escandallo": {
            "fuertes": ["receta", "ingrediente", "cantidad", "unidad", "merma"],
            "medias": ["racion", "raciones", "coste", "precio", "elaboracion", "familia"],
            "motivo": "Tiene estructura de receta con ingredientes, cantidades, unidades y mermas.",
        },
        "listado_articulos": {
            "fuertes": ["articulo", "producto", "codigo", "unidad", "familia"],
            "medias": ["proveedor", "precio", "categoria", "alergeno", "stock minimo"],
            "motivo": "Tiene estructura de listado maestro de productos/artículos.",
        },
        "inventario": {
            "fuertes": ["stock", "inventario", "cantidad", "unidad", "ubicacion"],
            "medias": ["caducidad", "lote", "camara", "almacen", "producto", "articulo"],
            "motivo": "Tiene estructura de inventario con cantidades, ubicación o caducidad.",
        },
        "compras": {
            "fuertes": ["proveedor", "compra", "pedido", "precio", "cantidad"],
            "medias": ["fecha", "factura", "importe", "total", "articulo", "producto", "unidad"],
            "motivo": "Tiene estructura de compras/pedidos con proveedor, cantidades y precios.",
        },
        "produccion": {
            "fuertes": ["produccion", "elaboracion", "fecha", "responsable", "tiempo"],
            "medias": ["tarea", "fase", "receta", "cantidad", "estado", "prioridad"],
            "motivo": "Tiene estructura de planificación o control de producción.",
        },
        "proveedores": {
            "fuertes": ["proveedor", "telefono", "email", "contacto"],
            "medias": ["direccion", "cif", "comercial", "categoria", "producto"],
            "motivo": "Tiene estructura de listado de proveedores/contactos.",
        },
    }

    SINONIMOS = {
        "articulos": "articulo",
        "artículo": "articulo",
        "artículos": "articulo",
        "producto": "producto",
        "productos": "producto",
        "ingredientes": "ingrediente",
        "uds": "unidad",
        "ud": "unidad",
        "u": "unidad",
        "kg": "unidad",
        "l": "unidad",
        "precio unitario": "precio",
        "p unit": "precio",
        "p.unit": "precio",
        "coste unitario": "coste",
        "familias": "familia",
        "categoría": "categoria",
        "categorias": "categoria",
        "ubicación": "ubicacion",
        "camara": "camara",
        "cámara": "camara",
        "fecha caducidad": "caducidad",
        "f caducidad": "caducidad",
        "recetas": "receta",
        "ración": "racion",
        "raciones": "raciones",
        "mermas": "merma",
    }

    def __init__(self, lector_excel):
        self.lector_excel = lector_excel

    def detectar_archivo(
        self,
        ruta_archivo: str,
        filas_preview: int = 10,
        exportar_json: bool = True,
    ) -> Dict[str, Any]:
        analisis = self.lector_excel.analizar_archivo(
            ruta_archivo=ruta_archivo,
            filas_preview=filas_preview,
            exportar_json=exportar_json,
        )
        return self.detectar_desde_analisis(analisis)

    def detectar_desde_analisis(self, analisis: Dict[str, Any]) -> Dict[str, Any]:
        detecciones_hojas = []
        conteo_tipos: Dict[str, int] = {}
        suma_confianza: Dict[str, float] = {}

        for hoja in analisis.get("hojas", []):
            det = self._detectar_hoja(hoja)
            detecciones_hojas.append(det)
            conteo_tipos[det.tipo_principal] = conteo_tipos.get(det.tipo_principal, 0) + 1
            suma_confianza[det.tipo_principal] = suma_confianza.get(det.tipo_principal, 0.0) + det.confianza

        tipo_principal = "desconocido"
        confianza = 0.0
        if detecciones_hojas:
            # Tipo principal: el que tenga mayor suma de confianza.
            tipo_principal = max(suma_confianza, key=suma_confianza.get)
            confianza = round(suma_confianza[tipo_principal] / max(1, conteo_tipos[tipo_principal]), 2)

        doc = DeteccionDocumentoExcel(
            archivo=analisis.get("archivo", ""),
            nombre_archivo=analisis.get("nombre_archivo", ""),
            tipo_principal=tipo_principal,
            confianza=confianza,
            hojas=detecciones_hojas,
            resumen={
                "total_hojas": len(detecciones_hojas),
                "tipos_detectados": conteo_tipos,
                "requiere_revision": any(h.confianza < 70 for h in detecciones_hojas),
            },
        )

        datos = doc.to_dict()
        datos["lectura_host_ai"] = (
            f"Documento detectado como {tipo_principal} con confianza {confianza}%."
            if tipo_principal != "desconocido"
            else "No se ha podido detectar el tipo de documento con suficiente confianza."
        )
        return datos

    def _detectar_hoja(self, hoja: Dict[str, Any]) -> DeteccionHojaExcel:
        columnas = [
            self._normalizar(c.get("nombre_detectado", ""))
            for c in hoja.get("columnas_detectadas", [])
        ]
        columnas_texto = " ".join(columnas)

        candidatos: List[TipoDocumentoDetectado] = []
        for tipo, regla in self.REGLAS.items():
            puntos = 0
            max_puntos = 0
            motivos = []
            cols_detectadas = []

            for clave in regla["fuertes"]:
                max_puntos += 20
                if self._contiene_clave(columnas, columnas_texto, clave):
                    puntos += 20
                    cols_detectadas.append(clave)
                    motivos.append(f"Columna fuerte detectada: {clave}")

            for clave in regla["medias"]:
                max_puntos += 8
                if self._contiene_clave(columnas, columnas_texto, clave):
                    puntos += 8
                    cols_detectadas.append(clave)
                    motivos.append(f"Columna secundaria detectada: {clave}")

            # Bonus por combinaciones muy claras.
            bonus = self._bonus_por_tipo(tipo, columnas_texto)
            puntos += bonus
            max_puntos += 20
            if bonus:
                motivos.append(f"Combinación de columnas típica de {tipo}.")

            confianza = round(min(100.0, (puntos / max(1, max_puntos)) * 100), 2)
            if confianza >= 10:
                candidatos.append(TipoDocumentoDetectado(
                    tipo=tipo,
                    confianza=confianza,
                    motivos=motivos or [regla["motivo"]],
                    columnas_clave_detectadas=sorted(set(cols_detectadas)),
                ))

        candidatos.sort(key=lambda c: c.confianza, reverse=True)

        avisos = []
        if not candidatos or candidatos[0].confianza < 35:
            tipo = "desconocido"
            confianza = candidatos[0].confianza if candidatos else 0.0
            avisos.append("Confianza baja. Requiere revisión manual.")
        else:
            tipo = candidatos[0].tipo
            confianza = candidatos[0].confianza
            if len(candidatos) > 1 and (candidatos[0].confianza - candidatos[1].confianza) < 12:
                avisos.append(
                    f"Detección ambigua entre {candidatos[0].tipo} y {candidatos[1].tipo}."
                )

        return DeteccionHojaExcel(
            hoja=hoja.get("nombre", ""),
            filas=hoja.get("filas", 0),
            columnas=hoja.get("columnas", 0),
            tipo_principal=tipo,
            confianza=confianza,
            candidatos=candidatos[:5],
            avisos=avisos,
        )

    def _normalizar(self, texto: str) -> str:
        texto = str(texto or "").strip().lower()
        texto = "".join(
            c for c in unicodedata.normalize("NFD", texto)
            if unicodedata.category(c) != "Mn"
        )
        texto = texto.replace("_", " ").replace("-", " ").replace(".", " ")
        texto = " ".join(texto.split())
        return self.SINONIMOS.get(texto, texto)

    def _contiene_clave(self, columnas: List[str], columnas_texto: str, clave: str) -> bool:
        clave_n = self._normalizar(clave)
        if clave_n in columnas:
            return True
        return clave_n in columnas_texto

    def _bonus_por_tipo(self, tipo: str, columnas_texto: str) -> int:
        combos = {
            "escandallo": [["receta", "ingrediente", "cantidad"], ["ingrediente", "merma", "unidad"]],
            "listado_articulos": [["articulo", "unidad", "familia"], ["producto", "proveedor", "precio"]],
            "inventario": [["stock", "ubicacion", "caducidad"], ["producto", "cantidad", "ubicacion"]],
            "compras": [["proveedor", "precio", "cantidad"], ["factura", "importe", "fecha"]],
            "produccion": [["elaboracion", "responsable", "tiempo"], ["tarea", "fecha", "estado"]],
            "proveedores": [["proveedor", "telefono", "email"], ["contacto", "proveedor", "direccion"]],
        }
        for combo in combos.get(tipo, []):
            if all(self._normalizar(c) in columnas_texto for c in combo):
                return 20
        return 0
