from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineImportadorEscandallosExcel(BasePipeline):
    nombre = "importador_escandallos_excel"
    descripcion = "Pipeline para importar escandallos desde Excel."
    acciones_soportadas = ["vista_previa", "importar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "vista_previa":
            datos = self.core.importador_escandallos_excel.vista_previa(
                ruta_archivo=p["ruta_archivo"],
                filas_preview=p.get("filas_preview", 20),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Revisar escandallos detectados antes de importar."],
                requiere_aprobacion=bool(datos.get("errores")),
            )

        if solicitud.accion == "importar":
            datos = self.core.importador_escandallos_excel.importar(
                ruta_archivo=p["ruta_archivo"],
                filas_preview=p.get("filas_preview", 50),
                reemplazar=p.get("reemplazar", True),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Calcular escandallos o revisar artículos nuevos."],
                requiere_aprobacion=bool(datos.get("errores")),
            )

        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
