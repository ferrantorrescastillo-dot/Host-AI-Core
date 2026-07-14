from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineSelectorInteligenteMotores308(BasePipeline):
    nombre = 'selector_inteligente_motores_308'
    descripcion = 'Selecciona automáticamente el motor Host AI adecuado a partir de una intención conversacional.'
    acciones_soportadas = ['seleccionar', 'seleccionar_desde_conversacion']

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros or {}
        if solicitud.accion == 'seleccionar':
            d = self.core.selector_inteligente_motores_308.seleccionar(p.get('texto',''), p.get('analisis'), p.get('contexto'))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], d.get('requiere_confirmacion', False))
        if solicitud.accion == 'seleccionar_desde_conversacion':
            d = self.core.selector_inteligente_motores_308.seleccionar_desde_conversacion(p.get('conversacion', {}))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], d.get('requiere_confirmacion', False))
        return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
