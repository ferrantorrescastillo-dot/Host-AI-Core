from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineConflictosExcel(BasePipeline):
    nombre = "conflictos_excel"
    descripcion = "Pipeline para detectar y registrar decisiones sobre conflictos de importación Excel."
    acciones_soportadas = ["analizar", "resumen", "resolver"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "analizar":
            datos = self.core.resolutor_conflictos_excel.analizar_archivo(
                ruta_archivo=p["ruta_archivo"],
                filas_preview=p.get("filas_preview", 500),
            )
            return ResultadoPipeline(
                ok=True,
                pipeline=self.nombre,
                accion=solicitud.accion,
                mensaje=datos["lectura_host_ai"],
                datos=datos,
                acciones_recomendadas=["Resolver conflictos críticos antes de importar."] if datos.get("criticos") else ["Revisar avisos antes de importar."],
                requiere_aprobacion=datos.get("total_conflictos", 0) > 0,
            )

        if solicitud.accion == "resumen":
            datos = self.core.resolutor_conflictos_excel.resumen_ultimo_informe()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        if solicitud.accion == "resolver":
            datos = self.core.resolutor_conflictos_excel.resolver_conflicto(
                conflicto_id=p["conflicto_id"],
                decision=p["decision"],
            )
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
