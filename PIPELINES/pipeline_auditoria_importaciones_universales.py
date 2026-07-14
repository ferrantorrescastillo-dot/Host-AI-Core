from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineAuditoriaImportacionesUniversales(BasePipeline):
    nombre = "auditoria_importaciones_universales"
    descripcion = "Auditoría y log de importaciones universales de facturas."
    acciones_soportadas = ["registrar", "listar", "resumen", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "registrar":
            d = self.core.auditoria_importaciones_universales.registrar_resultado(p["resultado"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "listar":
            d = self.core.auditoria_importaciones_universales.listar(p.get("estado", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "resumen":
            d = self.core.auditoria_importaciones_universales.resumen()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "exportar":
            d = self.core.auditoria_importaciones_universales.exportar()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
