from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineGeneradorInteligenteRespuestas308(BasePipeline):
    nombre = 'generador_inteligente_respuestas_308'
    descripcion = 'Convierte resultados técnicos de Host AI en respuestas naturales y operativas.'
    acciones_soportadas = ['generar', 'generar_desde_texto']

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros or {}
        if solicitud.accion == 'generar':
            d = self.core.generador_inteligente_respuestas_308.generar(p.get('resultado'), p.get('seleccion'), p.get('tono','profesional'))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, d.get('advertencias', []), False)
        if solicitud.accion == 'generar_desde_texto':
            d = self.core.generador_inteligente_respuestas_308.generar_desde_texto(p.get('texto',''), p.get('contexto'))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, d.get('advertencias', []), False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
