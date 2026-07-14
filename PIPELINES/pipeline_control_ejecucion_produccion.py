from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineControlEjecucionProduccion(BasePipeline):
    nombre = 'control_ejecucion_produccion'
    descripcion = 'Controla avance real de producción frente a plan/asignación y detecta desviaciones.'
    acciones_soportadas = ['controlar', 'exportar']
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == 'controlar':
            d = self.core.control_ejecucion_produccion.controlar_ejecucion(p.get('planificacion'), p.get('asignacion'), p.get('avance'), p.get('minuto_actual', 0))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        if solicitud.accion == 'exportar':
            d = self.core.control_ejecucion_produccion.exportar_control(p['control'], p.get('nombre',''))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
