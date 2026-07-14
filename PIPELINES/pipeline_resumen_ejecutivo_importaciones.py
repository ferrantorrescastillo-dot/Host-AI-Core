from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineResumenEjecutivoImportaciones(BasePipeline):
    nombre = "resumen_ejecutivo_importaciones"
    descripcion = "Genera resumen ejecutivo de importaciones universales."
    acciones_soportadas = ["generar", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "generar":
            d = self.core.resumen_ejecutivo_importaciones.generar_resumen(p.get("ultimas", 10))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], bool(d.get("avisos")))
        if solicitud.accion == "exportar":
            d = self.core.resumen_ejecutivo_importaciones.exportar_resumen(p["resumen"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
