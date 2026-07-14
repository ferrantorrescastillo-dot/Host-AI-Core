from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineAnalizadorInteligenteProduccion(BasePipeline):
    nombre = 'analizador_inteligente_produccion'
    descripcion = 'Analiza elaboraciones, tiempos, recursos, prioridades y carga operativa de producción.'
    acciones_soportadas = ['analizar', 'exportar']
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == 'analizar':
            d = self.core.analizador_inteligente_produccion.analizar_produccion(p.get('elaboraciones'), p.get('jornada_horas', 7.5), p.get('cocineros', 3))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        if solicitud.accion == 'exportar':
            d = self.core.analizador_inteligente_produccion.exportar_analisis(p['analisis'], p.get('nombre',''))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
