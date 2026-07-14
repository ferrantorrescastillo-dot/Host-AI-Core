from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineImportadorArticulosExcel(BasePipeline):
    nombre = "importador_articulos_excel"
    descripcion = "Pipeline para importar listados de artículos desde Excel."
    acciones_soportadas = ["vista_previa", "importar", "listar_articulos"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "vista_previa":
            datos = self.core.importador_articulos_excel.vista_previa(
                ruta_archivo=p["ruta_archivo"],
                filas_preview=p.get("filas_preview", 50),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Revisar artículos detectados antes de importar."],
                requiere_aprobacion=bool(datos.get("errores")),
            )

        if solicitud.accion == "importar":
            datos = self.core.importador_articulos_excel.importar(
                ruta_archivo=p["ruta_archivo"],
                filas_preview=p.get("filas_preview", 500),
                actualizar_existentes=p.get("actualizar_existentes", True),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Revisar precios registrados y familias detectadas."],
                requiere_aprobacion=bool(datos.get("errores")),
            )

        if solicitud.accion == "listar_articulos":
            datos = self.core.importador_articulos_excel.listar_articulos()
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=[],
                requiere_aprobacion=False,
            )

        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
