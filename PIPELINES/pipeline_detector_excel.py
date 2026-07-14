from __future__ import annotations

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineDetectorExcel(BasePipeline):
    nombre = "detector_excel"
    descripcion = "Pipeline de detección inteligente de tipo de documento Excel."
    acciones_soportadas = [
        "detectar_archivo",
        "detectar_desde_analisis",
    ]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "detectar_archivo":
            datos = self.core.detector_excel.detectar_archivo(
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
                acciones_recomendadas=[] if not datos.get("resumen", {}).get("requiere_revision") else ["Revisar detección manualmente."],
                requiere_aprobacion=datos.get("resumen", {}).get("requiere_revision", False),
            )

        if solicitud.accion == "detectar_desde_analisis":
            datos = self.core.detector_excel.detectar_desde_analisis(
                analisis=p["analisis"],
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=[] if not datos.get("resumen", {}).get("requiere_revision") else ["Revisar detección manualmente."],
                requiere_aprobacion=datos.get("resumen", {}).get("requiere_revision", False),
            )

        return ResultadoPipeline(
            ok=False,
            pipeline=self.nombre,
            accion=solicitud.accion,
            mensaje="Acción no implementada.",
            errores=[f"Acción no implementada: {solicitud.accion}"],
        )
