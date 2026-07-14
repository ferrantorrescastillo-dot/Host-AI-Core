from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineAsistenteImportacionExcel(BasePipeline):
    nombre = "asistente_importacion_excel"
    descripcion = "Pipeline asistido para preparar y ejecutar importaciones Excel completas."
    acciones_soportadas = ["preparar", "ejecutar", "listar_sesiones"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "preparar":
            datos = self.core.asistente_importacion_excel.preparar_importacion(
                ruta_archivo=p["ruta_archivo"],
                filas_preview=p.get("filas_preview", 500),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Ejecutar importación si está lista."] if datos.get("estado") == "lista_para_importar" else ["Resolver errores/conflictos antes de importar."],
                requiere_aprobacion=datos.get("estado") != "lista_para_importar",
            )

        if solicitud.accion == "ejecutar":
            datos = self.core.asistente_importacion_excel.ejecutar_importacion(
                sesion_id=p["sesion_id"],
                importador=p.get("importador", "auto"),
                forzar=p.get("forzar", False),
                filas_preview=p.get("filas_preview", 1000),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Revisar base de datos/stock/escandallos tras importar."],
                requiere_aprobacion=False,
            )

        if solicitud.accion == "listar_sesiones":
            datos = self.core.asistente_importacion_excel.listar_sesiones()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
