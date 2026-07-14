from __future__ import annotations

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineExcel(BasePipeline):
    nombre = "excel"
    descripcion = "Pipeline de importación Excel: lectura universal y análisis de hojas."
    acciones_soportadas = [
        "analizar_excel",
        "exportar_analisis",
    ]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "analizar_excel":
            datos = self.core.lector_excel.analizar_archivo(
                ruta_archivo=p["ruta_archivo"],
                filas_preview=p.get("filas_preview", 10),
                exportar_json=p.get("exportar_json", True),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Revisar hojas detectadas antes de importar."],
                requiere_aprobacion=False,
            )

        if solicitud.accion == "exportar_analisis":
            datos = self.core.lector_excel.exportar_analisis_json(
                analisis=p["analisis"],
                nombre=p.get("nombre", ""),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=[],
                requiere_aprobacion=False,
            )

        return ResultadoPipeline(
            ok=False,
            pipeline=self.nombre,
            accion=solicitud.accion,
            mensaje="Acción no implementada.",
            errores=[f"Acción no implementada: {solicitud.accion}"],
        )
