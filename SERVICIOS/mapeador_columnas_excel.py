from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Any
import json
import unicodedata
from MODELOS.mapeo_columnas_excel import MapeoColumna, MapeoHojaExcel, MapeoDocumentoExcel

class MapeadorColumnasExcel:
    """
    Mapeador Inteligente de Columnas v3.0.2.3.

    Convierte columnas reales de Excel en campos canónicos:
    ARTICULO, RECETA, INGREDIENTE, CANTIDAD, UNIDAD, PRECIO, PROVEEDOR, etc.
    Aprende sinónimos nuevos y los guarda en DATOS/diccionarios/diccionario_columnas_excel.json.
    """

    CAMPOS_CANONICOS = {
        "ARTICULO": ["articulo", "artículo", "producto", "nombre producto", "descripcion", "descripción", "item", "referencia", "nombre"],
        "CODIGO": ["codigo", "código", "cod", "ref", "referencia", "sku", "id articulo", "id"],
        "RECETA": ["receta", "plato", "elaboracion", "elaboración", "preparacion", "preparación"],
        "INGREDIENTE": ["ingrediente", "producto", "articulo", "materia prima", "mp"],
        "CANTIDAD": ["cantidad", "cant", "qty", "q", "stock", "existencias", "unidades"],
        "UNIDAD": ["unidad", "ud", "uds", "u", "kg", "g", "l", "litros", "ml", "racion", "ración"],
        "PRECIO": ["precio", "p unit", "p.unit", "precio unitario", "coste", "coste unitario", "importe unitario", "€/kg", "eur kg"],
        "TOTAL": ["total", "importe", "subtotal", "base imponible"],
        "MERMA": ["merma", "mermas", "% merma", "rendimiento", "perdida", "pérdida"],
        "PROVEEDOR": ["proveedor", "supplier", "vendedor", "empresa"],
        "FAMILIA": ["familia", "categoria", "categoría", "grupo", "subgrupo", "tipo"],
        "UBICACION": ["ubicacion", "ubicación", "almacen", "almacén", "camara", "cámara", "zona"],
        "CADUCIDAD": ["caducidad", "fecha caducidad", "f caducidad", "vencimiento"],
        "FECHA": ["fecha", "dia", "día", "date"],
        "RESPONSABLE": ["responsable", "trabajador", "cocinero", "persona"],
        "TIEMPO": ["tiempo", "duracion", "duración", "minutos", "horas"],
        "OBSERVACIONES": ["observaciones", "notas", "comentarios", "obs"],
        "STOCK_MINIMO": ["stock minimo", "stock mínimo", "minimo", "mínimo", "min", "stock min"],
        "ALERGENOS": ["alergenos", "alérgenos", "alergeno", "alérgeno"],
        "LOTE": ["lote", "batch", "partida"],
    }

    OBLIGATORIAS_POR_TIPO = {
        "escandallo": ["RECETA", "INGREDIENTE", "CANTIDAD", "UNIDAD"],
        "listado_articulos": ["ARTICULO", "UNIDAD"],
        "inventario": ["ARTICULO", "CANTIDAD", "UNIDAD"],
        "compras": ["PROVEEDOR", "ARTICULO", "CANTIDAD", "PRECIO"],
        "produccion": ["RECETA", "FECHA"],
        "proveedores": ["PROVEEDOR"],
    }

    def __init__(self, base_dir: Path, detector_excel):
        self.base_dir = Path(base_dir)
        self.detector_excel = detector_excel
        self.diccionario_path = self.base_dir / "DATOS" / "diccionarios" / "diccionario_columnas_excel.json"
        self.diccionario_path.parent.mkdir(parents=True, exist_ok=True)
        self.diccionario = self._cargar_diccionario()

    def mapear_archivo(self, ruta_archivo: str, filas_preview: int = 10) -> Dict[str, Any]:
        deteccion = self.detector_excel.detectar_archivo(ruta_archivo, filas_preview=filas_preview, exportar_json=True)
        return self.mapear_desde_deteccion(deteccion)

    def mapear_desde_deteccion(self, deteccion: Dict[str, Any]) -> Dict[str, Any]:
        hojas_mapeadas = []
        # Necesitamos análisis completo con columnas. La detección ya no contiene todas las columnas originales.
        # Si viene de detectar_archivo, reanalizamos por archivo para obtener columnas.
        analisis = self.detector_excel.lector_excel.analizar_archivo(deteccion["archivo"], exportar_json=False)

        tipos_por_hoja = {h["hoja"]: h.get("tipo_principal", "desconocido") for h in deteccion.get("hojas", [])}

        for hoja in analisis.get("hojas", []):
            tipo_doc = tipos_por_hoja.get(hoja["nombre"], "desconocido")
            hojas_mapeadas.append(self._mapear_hoja(hoja, tipo_doc))

        doc = MapeoDocumentoExcel(
            archivo=deteccion.get("archivo", ""),
            nombre_archivo=deteccion.get("nombre_archivo", ""),
            hojas=hojas_mapeadas,
        )
        datos = doc.to_dict()
        datos["lectura_host_ai"] = f"Mapeo de columnas completado para {len(hojas_mapeadas)} hojas."
        return datos

    def aprender_columna(self, columna_original: str, campo_canonico: str) -> Dict[str, Any]:
        campo = campo_canonico.strip().upper()
        if campo not in self.CAMPOS_CANONICOS and campo not in self.diccionario.get("aprendidos", {}):
            # Permitimos nuevos campos, pero los marcamos.
            self.diccionario.setdefault("campos_personalizados", []).append(campo)

        clave = self._normalizar(columna_original)
        self.diccionario.setdefault("aprendidos", {})[clave] = campo
        self._guardar_diccionario()
        return {
            "columna_original": columna_original,
            "normalizada": clave,
            "campo_canonico": campo,
            "lectura_host_ai": f"Columna aprendida: '{columna_original}' -> {campo}.",
        }

    def listar_diccionario(self) -> Dict[str, Any]:
        return {
            "campos_canonicos": self.CAMPOS_CANONICOS,
            "aprendidos": self.diccionario.get("aprendidos", {}),
            "campos_personalizados": self.diccionario.get("campos_personalizados", []),
            "lectura_host_ai": f"Diccionario de columnas: {len(self.CAMPOS_CANONICOS)} campos base y {len(self.diccionario.get('aprendidos', {}))} aprendidos.",
        }

    def exportar_diccionario(self) -> Dict[str, Any]:
        self._guardar_diccionario()
        return {"archivo": str(self.diccionario_path), "lectura_host_ai": "Diccionario de columnas exportado."}

    def _mapear_hoja(self, hoja: Dict[str, Any], tipo_documento: str) -> MapeoHojaExcel:
        mapeos = []
        desconocidas = []
        campos_detectados = set()

        for col in hoja.get("columnas_detectadas", []):
            m = self._mapear_columna(col)
            if m.campo_canonico == "DESCONOCIDO":
                desconocidas.append({
                    "columna_original": m.columna_original,
                    "letra": m.letra,
                    "tipo_detectado": m.tipo_detectado,
                    "ejemplos": m.ejemplos,
                })
            else:
                campos_detectados.add(m.campo_canonico)
            mapeos.append(m)

        obligatorias = self.OBLIGATORIAS_POR_TIPO.get(tipo_documento, [])
        faltantes = [c for c in obligatorias if c not in campos_detectados]

        conocidas = [m.confianza for m in mapeos if m.campo_canonico != "DESCONOCIDO"]
        confianza_media = round(sum(conocidas) / len(conocidas), 2) if conocidas else 0.0

        return MapeoHojaExcel(
            hoja=hoja.get("nombre", ""),
            tipo_documento=tipo_documento,
            mapeos=mapeos,
            desconocidas=desconocidas,
            obligatorias_faltantes=faltantes,
            confianza_media=confianza_media,
        )

    def _mapear_columna(self, col: Dict[str, Any]) -> MapeoColumna:
        nombre = col.get("nombre_detectado", "")
        normal = self._normalizar(nombre)

        aprendidos = self.diccionario.get("aprendidos", {})
        if normal in aprendidos:
            return MapeoColumna(nombre, aprendidos[normal], 100.0, "aprendido", ["Coincidencia aprendida por el usuario."], col.get("tipo_detectado", ""), col.get("letra", ""), col.get("ejemplos", []))

        mejor_campo = "DESCONOCIDO"
        mejor_score = 0.0
        motivos = []

        for campo, sinonimos in self.CAMPOS_CANONICOS.items():
            for sinonimo in sinonimos:
                s = self._normalizar(sinonimo)
                score = self._score(normal, s)
                if score > mejor_score:
                    mejor_score = score
                    mejor_campo = campo
                    motivos = [f"Coincide con sinónimo '{sinonimo}' de {campo}."]

        if mejor_score < 55:
            return MapeoColumna(nombre, "DESCONOCIDO", round(mejor_score, 2), "desconocido", ["No hay coincidencia suficiente."], col.get("tipo_detectado", ""), col.get("letra", ""), col.get("ejemplos", []))

        return MapeoColumna(nombre, mejor_campo, round(mejor_score, 2), "automatico", motivos, col.get("tipo_detectado", ""), col.get("letra", ""), col.get("ejemplos", []))

    def _score(self, texto: str, sinonimo: str) -> float:
        if texto == sinonimo:
            return 100.0
        if sinonimo in texto or texto in sinonimo:
            if len(sinonimo) <= 2 and texto != sinonimo:
                return 55.0
            return 85.0
        # Coincidencia por palabras
        palabras_t = set(texto.split())
        palabras_s = set(sinonimo.split())
        if not palabras_t or not palabras_s:
            return 0.0
        inter = len(palabras_t & palabras_s)
        union = len(palabras_t | palabras_s)
        return (inter / union) * 80

    def _normalizar(self, texto: str) -> str:
        texto = str(texto or "").strip().lower()
        texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
        texto = texto.replace("_", " ").replace("-", " ").replace(".", " ").replace("/", " ")
        texto = " ".join(texto.split())
        return texto

    def _cargar_diccionario(self) -> Dict[str, Any]:
        if self.diccionario_path.exists():
            try:
                return json.loads(self.diccionario_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"version": "3.0.2.3", "aprendidos": {}, "campos_personalizados": []}

    def _guardar_diccionario(self):
        self.diccionario_path.write_text(json.dumps(self.diccionario, ensure_ascii=False, indent=2), encoding="utf-8")
