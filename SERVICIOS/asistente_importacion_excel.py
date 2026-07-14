from __future__ import annotations
from typing import Dict, List, Any

from MODELOS.asistente_importacion_excel import SesionImportacionExcel, PasoImportacionExcel


class AsistenteImportacionExcel:
    """
    Host AI 3.0.2.8 - Asistente Completo de Importación Excel.

    Orquesta el flujo completo:
    1. Analizar Excel.
    2. Detectar tipo de documento.
    3. Mapear columnas.
    4. Detectar conflictos.
    5. Vista previa del importador correcto.
    6. Importar si no hay conflictos críticos.
    """

    def __init__(self, core):
        self.core = core
        self.sesiones: Dict[str, SesionImportacionExcel] = {}

    def preparar_importacion(self, ruta_archivo: str, filas_preview: int = 500) -> Dict[str, Any]:
        sesion = SesionImportacionExcel(archivo=str(ruta_archivo))
        pasos = []

        # 1. analizar
        try:
            analisis = self.core.lector_excel.analizar_archivo(
                ruta_archivo,
                filas_preview=filas_preview,
                exportar_json=True,
            )
            pasos.append(PasoImportacionExcel(
                nombre="analizar_excel",
                estado="ok",
                mensaje=analisis.get("lectura_host_ai", "Excel analizado."),
                datos={
                    "total_hojas": analisis.get("total_hojas"),
                    "total_filas": analisis.get("total_filas"),
                    "total_columnas": analisis.get("total_columnas"),
                    "json_exportado": analisis.get("json_exportado"),
                },
            ))
        except Exception as exc:
            pasos.append(PasoImportacionExcel("analizar_excel", "error", f"No se pudo analizar el Excel: {exc}"))
            sesion.estado = "bloqueada"
            sesion.pasos = pasos
            self.sesiones[sesion.id] = sesion
            return self._salida(sesion)

        # 2. detectar
        try:
            deteccion = self.core.detector_excel.detectar_desde_analisis(analisis)
            sesion.tipo_detectado = deteccion.get("tipo_principal", "desconocido")
            sesion.confianza = deteccion.get("confianza", 0.0)
            pasos.append(PasoImportacionExcel(
                nombre="detectar_documento",
                estado="ok" if sesion.tipo_detectado != "desconocido" else "revisar",
                mensaje=deteccion.get("lectura_host_ai", ""),
                datos=deteccion,
            ))
        except Exception as exc:
            pasos.append(PasoImportacionExcel("detectar_documento", "error", f"No se pudo detectar documento: {exc}"))
            deteccion = {"tipo_principal": "desconocido", "hojas": []}

        # 3. mapear
        try:
            mapeo = self.core.mapeador_columnas_excel.mapear_desde_deteccion(deteccion)
            desconocidas = sum(len(h.get("desconocidas", [])) for h in mapeo.get("hojas", []))
            faltantes = sum(len(h.get("obligatorias_faltantes", [])) for h in mapeo.get("hojas", []))
            estado = "ok" if faltantes == 0 else "revisar"
            pasos.append(PasoImportacionExcel(
                nombre="mapear_columnas",
                estado=estado,
                mensaje=f"Mapeo completado. Desconocidas: {desconocidas}, faltantes: {faltantes}.",
                datos={
                    "desconocidas": desconocidas,
                    "faltantes": faltantes,
                    "hojas": mapeo.get("hojas", []),
                },
            ))
        except Exception as exc:
            pasos.append(PasoImportacionExcel("mapear_columnas", "error", f"No se pudo mapear columnas: {exc}"))

        # 4. conflictos
        try:
            conflictos = self.core.resolutor_conflictos_excel.analizar_archivo(
                ruta_archivo,
                filas_preview=filas_preview,
            )
            estado = "ok"
            if conflictos.get("criticos", 0) > 0:
                estado = "error"
            elif conflictos.get("total_conflictos", 0) > 0:
                estado = "revisar"
            pasos.append(PasoImportacionExcel(
                nombre="analizar_conflictos",
                estado=estado,
                mensaje=conflictos.get("lectura_host_ai", ""),
                datos=conflictos,
            ))
        except Exception as exc:
            pasos.append(PasoImportacionExcel("analizar_conflictos", "revisar", f"No se pudieron analizar conflictos: {exc}"))
            conflictos = {"criticos": 0, "total_conflictos": 0}

        # 5. sugerir importadores y vistas previas
        sugeridos = self._sugerir_importadores(deteccion)
        sesion.importadores_sugeridos = sugeridos

        previews = {}
        for imp in sugeridos:
            try:
                preview = self._vista_previa_importador(imp, ruta_archivo, filas_preview)
                previews[imp] = {
                    "mensaje": preview.get("lectura_host_ai", ""),
                    "resumen": self._resumen_preview(imp, preview),
                }
            except Exception as exc:
                previews[imp] = {"error": str(exc)}

        pasos.append(PasoImportacionExcel(
            nombre="vista_previa_importacion",
            estado="ok" if previews else "revisar",
            mensaje=f"Importadores sugeridos: {', '.join(sugeridos) if sugeridos else 'ninguno'}.",
            datos=previews,
        ))

        sesion.pasos = pasos
        errores = [p for p in pasos if p.estado == "error"]
        criticos = int(conflictos.get("criticos", 0) or 0)
        if errores or criticos:
            sesion.estado = "bloqueada"
        elif sugeridos:
            sesion.estado = "lista_para_importar"
        else:
            sesion.estado = "bloqueada"

        self.sesiones[sesion.id] = sesion
        return self._salida(sesion)

    def ejecutar_importacion(
        self,
        sesion_id: str,
        importador: str = "auto",
        forzar: bool = False,
        filas_preview: int = 1000,
    ) -> Dict[str, Any]:
        if sesion_id not in self.sesiones:
            raise ValueError(f"No existe sesión de importación: {sesion_id}")
        sesion = self.sesiones[sesion_id]

        if sesion.estado == "bloqueada" and not forzar:
            return {
                **sesion.to_dict(),
                "lectura_host_ai": "La importación está bloqueada por conflictos o errores. Usa forzar=True solo si sabes lo que haces.",
            }

        elegido = importador
        if elegido == "auto":
            if not sesion.importadores_sugeridos:
                raise ValueError("No hay importador sugerido.")
            elegido = sesion.importadores_sugeridos[0]

        resultado = self._ejecutar_importador(elegido, sesion.archivo, filas_preview)
        sesion.resultado_importacion = resultado
        sesion.estado = "importada"
        sesion.pasos.append(PasoImportacionExcel(
            nombre="ejecutar_importacion",
            estado="ok",
            mensaje=resultado.get("lectura_host_ai", "Importación ejecutada."),
            datos={"importador": elegido, "resultado": resultado},
        ))
        self.sesiones[sesion.id] = sesion
        return self._salida(sesion)

    def listar_sesiones(self) -> Dict[str, Any]:
        sesiones = [s.to_dict() for s in self.sesiones.values()]
        return {
            "sesiones": sesiones,
            "total": len(sesiones),
            "lectura_host_ai": f"Sesiones de importación: {len(sesiones)}.",
        }

    def _sugerir_importadores(self, deteccion: Dict[str, Any]) -> List[str]:
        tipos = []
        for h in deteccion.get("hojas", []):
            t = h.get("tipo_principal")
            if t and t not in tipos and t != "desconocido":
                tipos.append(t)
        if not tipos:
            t = deteccion.get("tipo_principal")
            if t and t != "desconocido":
                tipos.append(t)

        salida = []
        if "escandallo" in tipos:
            salida.append("escandallos")
        if "inventario" in tipos:
            salida.append("inventario")
        if "listado_articulos" in tipos:
            salida.append("articulos")
        if "compras" in tipos:
            salida.append("articulos")

        # Refuerzo práctico: algunos inventarios se detectan como artículos
        # porque contienen Producto/Unidad/Precio. Si las columnas tienen
        # stock/cantidad + ubicación/caducidad, sugerimos inventario también.
        try:
            for h in deteccion.get("hojas", []):
                nombres = []
                # La detección no siempre trae columnas, pero los motivos/candidatos sí traen claves.
                for c in h.get("candidatos", []):
                    nombres.extend(c.get("columnas_clave_detectadas", []))
                claves = set(nombres)
                if ("cantidad" in claves or "stock" in claves) and ("ubicacion" in claves or "caducidad" in claves):
                    if "inventario" not in salida:
                        salida.insert(0, "inventario")
        except Exception:
            pass

        # Si solo hay artículos, pero el documento se llama inventario o hay hoja inventario, sugiere inventario.
        nombre_doc = str(deteccion.get("nombre_archivo", "")).lower()
        hojas = " ".join(str(h.get("hoja", "")).lower() for h in deteccion.get("hojas", []))
        if ("inventario" in nombre_doc or "inventario" in hojas) and "inventario" not in salida:
            salida.insert(0, "inventario")

        return salida

    def _vista_previa_importador(self, importador: str, ruta: str, filas_preview: int) -> Dict[str, Any]:
        if importador == "escandallos":
            return self.core.importador_escandallos_excel.vista_previa(ruta, filas_preview)
        if importador == "articulos":
            return self.core.importador_articulos_excel.vista_previa(ruta, filas_preview)
        if importador == "inventario":
            return self.core.importador_inventario_excel.vista_previa(ruta, filas_preview)
        raise ValueError(f"Importador no soportado: {importador}")

    def _ejecutar_importador(self, importador: str, ruta: str, filas_preview: int) -> Dict[str, Any]:
        if importador == "escandallos":
            return self.core.importador_escandallos_excel.importar(ruta, filas_preview=filas_preview, reemplazar=True)
        if importador == "articulos":
            return self.core.importador_articulos_excel.importar(ruta, filas_preview=filas_preview, actualizar_existentes=True)
        if importador == "inventario":
            return self.core.importador_inventario_excel.importar(ruta, filas_preview=filas_preview, crear_articulos=True, actualizar_stock=True)
        raise ValueError(f"Importador no soportado: {importador}")

    def _resumen_preview(self, importador: str, preview: Dict[str, Any]) -> Dict[str, Any]:
        if importador == "escandallos":
            return {
                "recetas_detectadas": preview.get("recetas_detectadas", 0),
                "lineas_importadas": preview.get("lineas_importadas", 0),
                "errores": len(preview.get("errores", [])),
            }
        if importador == "articulos":
            return {
                "articulos_detectados": preview.get("articulos_detectados", 0),
                "errores": len(preview.get("errores", [])),
            }
        if importador == "inventario":
            return {
                "lineas_detectadas": preview.get("lineas_detectadas", 0),
                "cambios": len(preview.get("cambios", [])),
                "errores": len(preview.get("errores", [])),
            }
        return {}

    def _salida(self, sesion: SesionImportacionExcel) -> Dict[str, Any]:
        datos = sesion.to_dict()
        if sesion.estado == "lista_para_importar":
            datos["lectura_host_ai"] = f"Importación preparada. Tipo: {sesion.tipo_detectado}. Lista para importar."
        elif sesion.estado == "importada":
            datos["lectura_host_ai"] = f"Importación ejecutada correctamente con {sesion.importadores_sugeridos}."
        else:
            datos["lectura_host_ai"] = f"Importación bloqueada o requiere revisión. Tipo: {sesion.tipo_detectado}."
        return datos
