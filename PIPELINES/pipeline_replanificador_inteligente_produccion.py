from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineReplanificadorInteligenteProduccion(BasePipeline):
    nombre = 'replanificador_inteligente_produccion'
    descripcion = 'Replanifica producción ante retrasos, bloqueos e incidencias operativas.'
    acciones_soportadas = ['replanificar', 'exportar']
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == 'replanificar':
            d = self.core.replanificador_inteligente_produccion.replanificar_produccion(p.get('control'), p.get('planificacion'), p.get('incidencias'), p.get('cocineros_disponibles', 3))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        if solicitud.accion == 'exportar':
            d = self.core.replanificador_inteligente_produccion.exportar_replanificacion(p['replanificacion'], p.get('nombre',''))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
