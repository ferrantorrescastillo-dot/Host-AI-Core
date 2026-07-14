from __future__ import annotations
from typing import Dict, List, Any
import re

from MODELOS.importacion_articulos_excel import (
    ArticuloImportadoExcel,
    ResultadoImportacionArticulos,
    ErrorImportacionArticulo,
)


class ImportadorArticulosExcel:
    """
    Importador de Artículos Excel v3.0.2.5.

    Importa listados maestros de artículos/productos.
    Se apoya en:
    - lector_excel
    - detector_excel
    - mapeador_columnas_excel

    En esta versión:
    - crea un registro interno simple de artículos importados
    - registra precios si hay precio
    - puede registrar stock mínimo y ubicación
    - guarda en persistencia si está disponible
    """

    def __init__(self, core):
        self.core = core
        self.articulos: Dict[str, ArticuloImportadoExcel] = {}

    def vista_previa(self, ruta_archivo: str, filas_preview: int = 50) -> Dict[str, Any]:
        return self._procesar(ruta_archivo, filas_preview=filas_preview, importar=False)

    def importar(self, ruta_archivo: str, filas_preview: int = 500, actualizar_existentes: bool = True) -> Dict[str, Any]:
        return self._procesar(
            ruta_archivo,
            filas_preview=filas_preview,
            importar=True,
            actualizar_existentes=actualizar_existentes,
        )

    def listar_articulos(self) -> Dict[str, Any]:
        articulos = [a.to_dict() for a in self.articulos.values()]
        return {
            "articulos": articulos,
            "total": len(articulos),
            "lectura_host_ai": f"Artículos importados en memoria: {len(articulos)}.",
        }

    def _procesar(self, ruta_archivo: str, filas_preview: int, importar: bool, actualizar_existentes: bool = True) -> Dict[str, Any]:
        deteccion = self.core.detector_excel.detectar_archivo(ruta_archivo, filas_preview=filas_preview, exportar_json=True)
        mapeo = self.core.mapeador_columnas_excel.mapear_desde_deteccion(deteccion)
        analisis = self.core.lector_excel.analizar_archivo(ruta_archivo, filas_preview=filas_preview, exportar_json=False)

        hojas_mapeo = {h["hoja"]: h for h in mapeo.get("hojas", [])}
        articulos: Dict[str, ArticuloImportadoExcel] = {}
        errores: List[ErrorImportacionArticulo] = []
        duplicados = 0
        importados = 0
        actualizados = 0
        precios_registrados = 0

        for hoja in analisis.get("hojas", []):
            nombre_hoja = hoja["nombre"]
            map_hoja = hojas_mapeo.get(nombre_hoja)
            if not map_hoja:
                continue

            es_articulos = (
                map_hoja.get("tipo_documento") == "listado_articulos"
                or self._parece_listado_articulos(map_hoja)
            )
            if not es_articulos:
                continue

            campo_por_columna = {
                m["columna_original"]: m["campo_canonico"]
                for m in map_hoja.get("mapeos", [])
                if m.get("campo_canonico") != "DESCONOCIDO"
            }

            for idx, fila in enumerate(hoja.get("vista_previa", []), start=2):
                normalizada = self._normalizar_fila(fila, campo_por_columna)

                nombre = str(
                    normalizada.get("ARTICULO", "")
                    or normalizada.get("INGREDIENTE", "")
                    or ""
                ).strip()
                codigo = str(normalizada.get("CODIGO", "") or "").strip()
                unidad = str(normalizada.get("UNIDAD", "") or "").strip()
                familia = str(normalizada.get("FAMILIA", "") or "").strip()
                proveedor = str(normalizada.get("PROVEEDOR", "") or "").strip()
                ubicacion = str(normalizada.get("UBICACION", "") or "").strip()
                alergenos = str(normalizada.get("ALERGENOS", "") or "").strip()
                precio = self._a_float(normalizada.get("PRECIO"), 0.0)
                stock_minimo = self._a_float(normalizada.get("STOCK_MINIMO") or normalizada.get("CANTIDAD"), 0.0)

                if not nombre:
                    if any(v not in [None, ""] for v in fila.values()):
                        errores.append(ErrorImportacionArticulo(nombre_hoja, idx, "Falta nombre de artículo.", fila))
                    continue

                if not unidad:
                    errores.append(ErrorImportacionArticulo(nombre_hoja, idx, f"Falta unidad para {nombre}.", fila, nivel="aviso"))

                articulo_id = codigo or self._articulo_id(nombre)
                if articulo_id in articulos:
                    duplicados += 1

                articulos[articulo_id] = ArticuloImportadoExcel(
                    nombre=nombre,
                    articulo_id=articulo_id,
                    unidad=unidad,
                    familia=familia,
                    proveedor=proveedor,
                    precio_unitario=precio,
                    stock_minimo=stock_minimo,
                    ubicacion=ubicacion,
                    codigo=codigo,
                    alergenos=alergenos,
                )

        if importar:
            for articulo_id, art in articulos.items():
                existe = articulo_id in self.articulos
                if existe and not actualizar_existentes:
                    duplicados += 1
                    errores.append(ErrorImportacionArticulo(
                        hoja="",
                        fila=0,
                        mensaje=f"Artículo ya existe y actualizar_existentes=False: {articulo_id}",
                        datos=art.to_dict(),
                        nivel="aviso",
                    ))
                    continue

                self.articulos[articulo_id] = art
                if existe:
                    actualizados += 1
                else:
                    importados += 1

                if art.precio_unitario > 0 and hasattr(self.core, "costes_inteligente"):
                    self.core.costes_inteligente.registrar_precio(
                        nombre=art.nombre,
                        precio_unitario=art.precio_unitario,
                        unidad=art.unidad or "ud",
                        articulo_id=art.articulo_id,
                        proveedor=art.proveedor,
                        familia=art.familia,
                    )
                    precios_registrados += 1

            if hasattr(self.core, "persistencia"):
                try:
                    self.core.persistencia.guardar_todo()
                except Exception:
                    pass

        resultado = ResultadoImportacionArticulos(
            archivo=str(ruta_archivo),
            modo="importar" if importar else "vista_previa",
            articulos_detectados=len(articulos),
            articulos_importados=importados,
            articulos_actualizados=actualizados,
            precios_registrados=precios_registrados,
            duplicados_detectados=duplicados,
            errores=errores,
            articulos=[a.to_dict() for a in articulos.values()],
        )
        datos = resultado.to_dict()
        datos["lectura_host_ai"] = self._lectura(resultado)
        return datos

    def _parece_listado_articulos(self, map_hoja: Dict[str, Any]) -> bool:
        campos = {m.get("campo_canonico") for m in map_hoja.get("mapeos", [])}
        if "ARTICULO" in campos and "UNIDAD" in campos:
            return True
        if "ARTICULO" in campos and ("PRECIO" in campos or "PROVEEDOR" in campos or "FAMILIA" in campos):
            return True
        return False

    def _normalizar_fila(self, fila: Dict[str, Any], campo_por_columna: Dict[str, str]) -> Dict[str, Any]:
        salida = {}
        for col_original, valor in fila.items():
            campo = campo_por_columna.get(col_original)
            if campo and campo != "DESCONOCIDO":
                # Si hay columnas repetidas, conserva la primera con dato.
                if campo not in salida or salida[campo] in [None, ""]:
                    salida[campo] = valor
        return salida

    def _a_float(self, valor, default: float = 0.0) -> float:
        if valor is None or valor == "":
            return default
        if isinstance(valor, (int, float)):
            return float(valor)
        limpio = str(valor).replace("€", "").replace("%", "").replace(",", ".").strip()
        try:
            return float(limpio)
        except Exception:
            return default

    def _slug(self, texto: str) -> str:
        texto = str(texto or "").upper().strip()
        texto = re.sub(r"[^A-Z0-9]+", "-", texto)
        texto = texto.strip("-")
        return texto[:40] or "SIN-NOMBRE"

    def _articulo_id(self, nombre: str) -> str:
        return f"ART-{self._slug(nombre)}"

    def _lectura(self, resultado: ResultadoImportacionArticulos) -> str:
        if resultado.modo == "vista_previa":
            return f"Vista previa artículos: {resultado.articulos_detectados} artículos detectados."
        return (
            f"Importación artículos completada: {resultado.articulos_importados} nuevos, "
            f"{resultado.articulos_actualizados} actualizados, {resultado.precios_registrados} precios registrados."
        )
