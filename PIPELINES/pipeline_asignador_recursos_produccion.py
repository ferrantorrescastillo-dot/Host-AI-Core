from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineAsignadorRecursosProduccion(BasePipeline):
    nombre = 'asignador_recursos_produccion'
    descripcion = 'Asigna tareas activas de producción a cocineros y recursos, detectando saturaciones.'
    acciones_soportadas = ['asignar', 'exportar']
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == 'asignar':
            d = self.core.asignador_recursos_produccion.asignar_recursos(p.get('elaboraciones'), p.get('planificacion'), p.get('cocineros', 3), p.get('jornada_horas', 7.5))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        if solicitud.accion == 'exportar':
            d = self.core.asignador_recursos_produccion.exportar_asignacion(p['asignacion'], p.get('nombre',''))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
