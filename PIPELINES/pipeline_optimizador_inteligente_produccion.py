from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineOptimizadorInteligenteProduccion(BasePipeline):
    nombre = 'optimizador_inteligente_produccion'
    descripcion = 'Optimiza secuencia, recursos, huecos y carga de cocineros en producción.'
    acciones_soportadas = ['optimizar', 'exportar']
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == 'optimizar':
            d = self.core.optimizador_inteligente_produccion.optimizar_produccion(p.get('planificacion'), p.get('asignacion'), p.get('control'), p.get('replanificacion'), p.get('elaboraciones'))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        if solicitud.accion == 'exportar':
            d = self.core.optimizador_inteligente_produccion.exportar_optimizacion(p['optimizacion'], p.get('nombre',''))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
