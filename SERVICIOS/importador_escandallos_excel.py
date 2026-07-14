from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import re

from MODELOS.importacion_escandallos_excel import ResultadoImportacionEscandallos, ErrorImportacionEscandallo


class ImportadorEscandallosExcel:
    """
    Importador de Escandallos Excel v3.0.2.4.

    Flujo:
    - Lee Excel.
    - Detecta documento.
    - Mapea columnas.
    - Identifica hojas de escandallo.
    - Agrupa líneas por receta.
    - Registra escandallos en MotorEscandallosInteligente.
    """

    def __init__(self, core):
        self.core = core

    def vista_previa(self, ruta_archivo: str, filas_preview: int = 20) -> Dict[str, Any]:
        return self._procesar(ruta_archivo, filas_preview=filas_preview, importar=False)

    def importar(self, ruta_archivo: str, filas_preview: int = 50, reemplazar: bool = True) -> Dict[str, Any]:
        return self._procesar(ruta_archivo, filas_preview=filas_preview, importar=True, reemplazar=reemplazar)

    def _procesar(self, ruta_archivo: str, filas_preview: int, importar: bool, reemplazar: bool = True) -> Dict[str, Any]:
        deteccion = self.core.detector_excel.detectar_archivo(ruta_archivo, filas_preview=filas_preview, exportar_json=True)
        mapeo = self.core.mapeador_columnas_excel.mapear_desde_deteccion(deteccion)
        analisis = self.core.lector_excel.analizar_archivo(ruta_archivo, filas_preview=filas_preview, exportar_json=False)

        hojas_mapeo = {h["hoja"]: h for h in mapeo.get("hojas", [])}
        recetas: Dict[str, Dict[str, Any]] = {}
        errores: List[ErrorImportacionEscandallo] = []
        articulos = set()
        lineas_importadas = 0

        for hoja in analisis.get("hojas", []):
            nombre_hoja = hoja["nombre"]
            map_hoja = hojas_mapeo.get(nombre_hoja)
            if not map_hoja:
                continue

            es_escandallo = (
                map_hoja.get("tipo_documento") == "escandallo"
                or self._parece_escandallo(map_hoja)
            )
            if not es_escandallo:
                continue

            campo_por_columna = {
                m["columna_original"]: m["campo_canonico"]
                for m in map_hoja.get("mapeos", [])
                if m.get("campo_canonico") != "DESCONOCIDO"
            }

            for idx, fila in enumerate(hoja.get("vista_previa", []), start=2):
                normalizada = self._normalizar_fila(fila, campo_por_columna)

                receta = str(normalizada.get("RECETA", "") or "").strip()
                ingrediente = str(normalizada.get("INGREDIENTE", "") or normalizada.get("ARTICULO", "") or "").strip()
                cantidad = self._a_float(normalizada.get("CANTIDAD"))
                unidad = str(normalizada.get("UNIDAD", "") or "").strip()
                merma = self._a_float(normalizada.get("MERMA"), default=0.0)
                precio = self._a_float(normalizada.get("PRECIO"), default=0.0)
                familia = str(normalizada.get("FAMILIA", "") or "").strip()
                proveedor = str(normalizada.get("PROVEEDOR", "") or "").strip()

                if not receta and not ingrediente:
                    continue

                if not receta:
                    errores.append(ErrorImportacionEscandallo(nombre_hoja, idx, "Falta nombre de receta.", fila))
                    continue
                if not ingrediente:
                    errores.append(ErrorImportacionEscandallo(nombre_hoja, idx, "Falta ingrediente.", fila))
                    continue
                if cantidad <= 0:
                    errores.append(ErrorImportacionEscandallo(nombre_hoja, idx, "Cantidad inválida o vacía.", fila))
                    continue
                if not unidad:
                    errores.append(ErrorImportacionEscandallo(nombre_hoja, idx, "Falta unidad.", fila))
                    continue

                receta_id = self._receta_id(receta)
                if receta_id not in recetas:
                    recetas[receta_id] = {
                        "receta_id": receta_id,
                        "nombre": receta,
                        "raciones_base": self._a_int(normalizada.get("RACIONES"), default=10),
                        "grupo": "Importado Excel",
                        "subgrupo": nombre_hoja,
                        "lineas": [],
                    }

                articulo_id = self._articulo_id(ingrediente)
                articulos.add(articulo_id)
                recetas[receta_id]["lineas"].append({
                    "nombre": ingrediente,
                    "cantidad": cantidad,
                    "unidad": unidad,
                    "tipo": "articulo",
                    "articulo_id": articulo_id,
                    "merma_porcentaje": merma,
                    "familia": familia,
                    "proveedor_preferente": proveedor,
                    "coste_unitario": precio,
                    "notas": f"Importado desde {nombre_hoja}",
                })
                lineas_importadas += 1

        escandallos = list(recetas.values())

        if importar:
            for esc in escandallos:
                try:
                    if reemplazar or esc["receta_id"] not in self.core.escandallos_inteligente.escandallos:
                        self.core.escandallos_inteligente.registrar_escandallo(**esc)
                    else:
                        errores.append(ErrorImportacionEscandallo(
                            hoja=esc.get("subgrupo", ""),
                            fila=0,
                            mensaje=f"Escandallo ya existe y reemplazar=False: {esc['receta_id']}",
                            datos=esc,
                            nivel="aviso",
                        ))
                except Exception as exc:
                    errores.append(ErrorImportacionEscandallo(
                        hoja=esc.get("subgrupo", ""),
                        fila=0,
                        mensaje=f"Error registrando escandallo {esc['receta_id']}: {exc}",
                        datos=esc,
                    ))

            if hasattr(self.core, "persistencia"):
                try:
                    self.core.persistencia.guardar_todo()
                except Exception:
                    pass

        resultado = ResultadoImportacionEscandallos(
            archivo=str(ruta_archivo),
            escandallos_importados=len(escandallos) if importar else 0,
            recetas_detectadas=len(escandallos),
            lineas_importadas=lineas_importadas,
            articulos_detectados=len(articulos),
            errores=errores,
            escandallos=escandallos,
            modo="importar" if importar else "vista_previa",
        )
        datos = resultado.to_dict()
        datos["lectura_host_ai"] = self._lectura(resultado)
        return datos

    def _parece_escandallo(self, map_hoja: Dict[str, Any]) -> bool:
        campos = {m.get("campo_canonico") for m in map_hoja.get("mapeos", [])}
        return {"RECETA", "INGREDIENTE", "CANTIDAD", "UNIDAD"}.issubset(campos)

    def _normalizar_fila(self, fila: Dict[str, Any], campo_por_columna: Dict[str, str]) -> Dict[str, Any]:
        salida = {}
        for col_original, valor in fila.items():
            campo = campo_por_columna.get(col_original)
            if campo and campo != "DESCONOCIDO":
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

    def _a_int(self, valor, default: int = 10) -> int:
        try:
            return int(float(valor))
        except Exception:
            return default

    def _slug(self, texto: str) -> str:
        texto = str(texto or "").upper().strip()
        texto = re.sub(r"[^A-Z0-9]+", "-", texto)
        texto = texto.strip("-")
        return texto[:40] or "SIN-NOMBRE"

    def _receta_id(self, nombre: str) -> str:
        return f"REC-{self._slug(nombre)}"

    def _articulo_id(self, nombre: str) -> str:
        return f"ART-{self._slug(nombre)}"

    def _lectura(self, resultado: ResultadoImportacionEscandallos) -> str:
        if resultado.modo == "vista_previa":
            return f"Vista previa escandallos: {resultado.recetas_detectadas} recetas y {resultado.lineas_importadas} líneas detectadas."
        return f"Importación escandallos completada: {resultado.escandallos_importados} escandallos importados, {len(resultado.errores)} avisos/errores."
