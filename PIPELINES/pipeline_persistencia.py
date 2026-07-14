from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelinePersistencia(BasePipeline):
    nombre = "persistencia"
    descripcion = "Pipeline de base de datos local y guardado de datos."
    acciones_soportadas = ["guardar_todo", "resumen_db", "snapshot", "limpiar_db"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "guardar_todo":
            d = self.core.persistencia.guardar_todo()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, ["Crear snapshot si es importante."], False)
        if solicitud.accion == "resumen_db":
            d = self.core.persistencia.resumen()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "snapshot":
            d = self.core.persistencia.snapshot(p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "limpiar_db":
            d = self.core.persistencia.limpiar()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["mensaje"], d, [], True)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
