from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineMapeadorColumnasExcel(BasePipeline):
    nombre = "mapeador_columnas_excel"
    descripcion = "Pipeline para mapear columnas Excel a campos canónicos de Host AI."
    acciones_soportadas = ["mapear_archivo", "mapear_desde_deteccion", "aprender_columna", "listar_diccionario", "exportar_diccionario"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "mapear_archivo":
            datos = self.core.mapeador_columnas_excel.mapear_archivo(p["ruta_archivo"], p.get("filas_preview", 10))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, ["Revisar columnas desconocidas antes de importar."], any(h.get("desconocidas") for h in datos.get("hojas", [])))

        if solicitud.accion == "mapear_desde_deteccion":
            datos = self.core.mapeador_columnas_excel.mapear_desde_deteccion(p["deteccion"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, ["Revisar columnas desconocidas antes de importar."], any(h.get("desconocidas") for h in datos.get("hojas", [])))

        if solicitud.accion == "aprender_columna":
            datos = self.core.mapeador_columnas_excel.aprender_columna(p["columna_original"], p["campo_canonico"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, ["Volver a mapear el documento."], False)

        if solicitud.accion == "listar_diccionario":
            datos = self.core.mapeador_columnas_excel.listar_diccionario()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        if solicitud.accion == "exportar_diccionario":
            datos = self.core.mapeador_columnas_excel.exportar_diccionario()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
