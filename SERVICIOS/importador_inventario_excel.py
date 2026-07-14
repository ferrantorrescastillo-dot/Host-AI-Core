from __future__ import annotations
from typing import Dict, List, Any
from datetime import datetime, date
import re

from MODELOS.importacion_inventario_excel import (
    LineaInventarioExcel,
    CambioInventarioExcel,
    ErrorImportacionInventario,
    ResultadoImportacionInventario,
)


class ImportadorInventarioExcel:
    """
    Importador de Inventario Excel v3.0.2.6.

    Importa inventarios reales:
    - producto/artículo
    - cantidad/stock
    - unidad
    - ubicación
    - caducidad
    - lote
    - proveedor
    - precio

    En esta versión actualiza el stock usando entradas de stock del motor existente.
    """

    def __init__(self, core):
        self.core = core
        self.ultimas_lineas: List[LineaInventarioExcel] = []

    def vista_previa(self, ruta_archivo: str, filas_preview: int = 100) -> Dict[str, Any]:
        return self._procesar(ruta_archivo, filas_preview=filas_preview, importar=False)

    def importar(
        self,
        ruta_archivo: str,
        filas_preview: int = 1000,
        crear_articulos: bool = True,
        actualizar_stock: bool = True,
    ) -> Dict[str, Any]:
        return self._procesar(
            ruta_archivo,
            filas_preview=filas_preview,
            importar=True,
            crear_articulos=crear_articulos,
            actualizar_stock=actualizar_stock,
        )

    def comparar_inventario(self, ruta_archivo: str, filas_preview: int = 1000) -> Dict[str, Any]:
        resultado = self._procesar(ruta_archivo, filas_preview=filas_preview, importar=False)
        return {
            "archivo": ruta_archivo,
            "cambios": resultado.get("cambios", []),
            "total_cambios": len(resultado.get("cambios", [])),
            "lectura_host_ai": f"Comparación de inventario: {len(resultado.get('cambios', []))} cambios detectados.",
        }

    def _procesar(
        self,
        ruta_archivo: str,
        filas_preview: int,
        importar: bool,
        crear_articulos: bool = True,
        actualizar_stock: bool = True,
    ) -> Dict[str, Any]:
        deteccion = self.core.detector_excel.detectar_archivo(ruta_archivo, filas_preview=filas_preview, exportar_json=True)
        mapeo = self.core.mapeador_columnas_excel.mapear_desde_deteccion(deteccion)
        analisis = self.core.lector_excel.analizar_archivo(ruta_archivo, filas_preview=filas_preview, exportar_json=False)

        hojas_mapeo = {h["hoja"]: h for h in mapeo.get("hojas", [])}
        lineas: List[LineaInventarioExcel] = []
        errores: List[ErrorImportacionInventario] = []
        cambios: List[CambioInventarioExcel] = []
        articulos_creados = 0
        stock_actualizado = 0

        for hoja in analisis.get("hojas", []):
            nombre_hoja = hoja["nombre"]
            map_hoja = hojas_mapeo.get(nombre_hoja)
            if not map_hoja:
                continue

            es_inventario = (
                map_hoja.get("tipo_documento") == "inventario"
                or self._parece_inventario(map_hoja)
            )
            if not es_inventario:
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
                cantidad = self._a_float(normalizada.get("CANTIDAD"), 0.0)
                unidad = str(normalizada.get("UNIDAD", "") or "").strip()
                familia = str(normalizada.get("FAMILIA", "") or "").strip()
                ubicacion = str(normalizada.get("UBICACION", "") or "").strip()
                caducidad = self._a_fecha_texto(normalizada.get("CADUCIDAD"))
                lote = str(normalizada.get("LOTE", "") or "").strip()
                proveedor = str(normalizada.get("PROVEEDOR", "") or "").strip()
                precio = self._a_float(normalizada.get("PRECIO"), 0.0)
                codigo = str(normalizada.get("CODIGO", "") or "").strip()

                if not nombre:
                    if any(v not in [None, ""] for v in fila.values()):
                        errores.append(ErrorImportacionInventario(nombre_hoja, idx, "Falta nombre de artículo.", fila))
                    continue
                if cantidad < 0:
                    errores.append(ErrorImportacionInventario(nombre_hoja, idx, f"Cantidad negativa para {nombre}.", fila))
                    continue
                if not unidad:
                    errores.append(ErrorImportacionInventario(nombre_hoja, idx, f"Falta unidad para {nombre}.", fila, nivel="aviso"))

                articulo_id = codigo or self._articulo_id(nombre)
                anterior = self._stock_actual_articulo(articulo_id, nombre)
                cambios.append(CambioInventarioExcel(
                    articulo_id=articulo_id,
                    nombre=nombre,
                    anterior=anterior,
                    nuevo=cantidad,
                    diferencia=round(cantidad - anterior, 4),
                    unidad=unidad or "ud",
                    accion="sin_cambios" if round(cantidad - anterior, 4) == 0 else "actualizar",
                ))

                lineas.append(LineaInventarioExcel(
                    nombre=nombre,
                    cantidad=cantidad,
                    unidad=unidad or "ud",
                    articulo_id=articulo_id,
                    familia=familia,
                    ubicacion=ubicacion,
                    caducidad=caducidad,
                    lote=lote,
                    proveedor=proveedor,
                    precio_unitario=precio,
                ))

        if importar:
            for linea in lineas:
                if crear_articulos and hasattr(self.core, "importador_articulos_excel"):
                    if linea.articulo_id not in self.core.importador_articulos_excel.articulos:
                        # Crea un artículo básico en el registro importado.
                        from MODELOS.importacion_articulos_excel import ArticuloImportadoExcel
                        self.core.importador_articulos_excel.articulos[linea.articulo_id] = ArticuloImportadoExcel(
                            nombre=linea.nombre,
                            articulo_id=linea.articulo_id,
                            unidad=linea.unidad,
                            familia=linea.familia,
                            proveedor=linea.proveedor,
                            precio_unitario=linea.precio_unitario,
                            ubicacion=linea.ubicacion,
                        )
                        articulos_creados += 1

                if linea.precio_unitario > 0 and hasattr(self.core, "costes_inteligente"):
                    self.core.costes_inteligente.registrar_precio(
                        nombre=linea.nombre,
                        precio_unitario=linea.precio_unitario,
                        unidad=linea.unidad,
                        articulo_id=linea.articulo_id,
                        proveedor=linea.proveedor,
                        familia=linea.familia,
                    )

                if actualizar_stock and hasattr(self.core, "stock"):
                    anterior = self._stock_actual_articulo(linea.articulo_id, linea.nombre)
                    diferencia = round(linea.cantidad - anterior, 4)
                    if diferencia > 0:
                        self.core.stock.registrar_entrada(
                            nombre=linea.nombre,
                            cantidad=diferencia,
                            unidad=linea.unidad,
                            articulo_id=linea.articulo_id,
                            familia=linea.familia,
                            ubicacion=linea.ubicacion,
                            proveedor=linea.proveedor,
                            caducidad=linea.caducidad,
                            motivo="Ajuste inventario Excel",
                        )
                        stock_actualizado += 1
                    elif diferencia < 0:
                        try:
                            self.core.stock.consumir(
                                nombre=linea.nombre,
                                cantidad=abs(diferencia),
                                unidad=linea.unidad,
                                articulo_id=linea.articulo_id,
                                motivo="Ajuste inventario Excel",
                            )
                            stock_actualizado += 1
                        except Exception as exc:
                            errores.append(ErrorImportacionInventario(
                                hoja="",
                                fila=0,
                                mensaje=f"No se pudo ajustar stock negativo de {linea.nombre}: {exc}",
                                datos=linea.to_dict(),
                                nivel="aviso",
                            ))

            self.ultimas_lineas = lineas

            if hasattr(self.core, "persistencia"):
                try:
                    self.core.persistencia.guardar_todo()
                except Exception:
                    pass

        resultado = ResultadoImportacionInventario(
            archivo=str(ruta_archivo),
            modo="importar" if importar else "vista_previa",
            lineas_detectadas=len(lineas),
            lineas_importadas=len(lineas) if importar else 0,
            articulos_creados=articulos_creados,
            stock_actualizado=stock_actualizado,
            cambios=cambios,
            lineas=[l.to_dict() for l in lineas],
            errores=errores,
        )
        datos = resultado.to_dict()
        datos["lectura_host_ai"] = self._lectura(resultado)
        return datos

    def _parece_inventario(self, map_hoja: Dict[str, Any]) -> bool:
        campos = {m.get("campo_canonico") for m in map_hoja.get("mapeos", [])}
        return "ARTICULO" in campos and "CANTIDAD" in campos and ("UNIDAD" in campos or "UBICACION" in campos or "CADUCIDAD" in campos)

    def _normalizar_fila(self, fila: Dict[str, Any], campo_por_columna: Dict[str, str]) -> Dict[str, Any]:
        salida = {}
        for col_original, valor in fila.items():
            campo = campo_por_columna.get(col_original)
            if campo and campo != "DESCONOCIDO":
                if campo not in salida or salida[campo] in [None, ""]:
                    salida[campo] = valor
        return salida

    def _stock_actual_articulo(self, articulo_id: str, nombre: str) -> float:
        if not hasattr(self.core, "stock"):
            return 0.0
        try:
            datos = self.core.stock.stock_actual()
            total = 0.0
            for item in datos.get("items", []):
                if item.get("articulo_id") == articulo_id or item.get("nombre", "").lower().strip() == nombre.lower().strip():
                    total += float(item.get("cantidad", 0.0) or 0.0)
            return round(total, 4)
        except Exception:
            return 0.0

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

    def _a_fecha_texto(self, valor) -> str:
        if valor is None or valor == "":
            return ""
        if isinstance(valor, (datetime, date)):
            return valor.date().isoformat() if isinstance(valor, datetime) else valor.isoformat()
        return str(valor).strip()

    def _slug(self, texto: str) -> str:
        texto = str(texto or "").upper().strip()
        texto = re.sub(r"[^A-Z0-9]+", "-", texto)
        texto = texto.strip("-")
        return texto[:40] or "SIN-NOMBRE"

    def _articulo_id(self, nombre: str) -> str:
        return f"ART-{self._slug(nombre)}"

    def _lectura(self, resultado: ResultadoImportacionInventario) -> str:
        if resultado.modo == "vista_previa":
            return f"Vista previa inventario: {resultado.lineas_detectadas} líneas detectadas."
        return (
            f"Importación inventario completada: {resultado.lineas_importadas} líneas, "
            f"{resultado.stock_actualizado} ajustes de stock, {resultado.articulos_creados} artículos creados."
        )
