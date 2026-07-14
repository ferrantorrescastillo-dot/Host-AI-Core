from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineAsistenteInteligenteHostAI308(BasePipeline):
    nombre = 'asistente_inteligente_host_ai_308'
    descripcion = 'Asistente final Host AI 3.0.8.7: une lenguaje natural, memoria, selección de motores, respuestas y automatización.'
    acciones_soportadas = ['responder', 'diagnosticar', 'exportar']

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros or {}
        svc = self.core.asistente_inteligente_host_ai_308
        if solicitud.accion == 'responder':
            d = svc.responder(p.get('texto',''), p.get('contexto'), p.get('ejecutar', False), p.get('confirmado', False))
        elif solicitud.accion == 'diagnosticar':
            d = svc.diagnosticar()
        elif solicitud.accion == 'exportar':
            d = svc.exportar(p.get('nombre',''))
        else:
            return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
        return ResultadoPipeline(True, self.nombre, solicitud.accion, d.get('lectura_host_ai','Asistente Host AI procesado.'), d, d.get('acciones_recomendadas', []), d.get('requiere_confirmacion', False))
