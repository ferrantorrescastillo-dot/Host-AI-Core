from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineAutomatizadorInteligente308(BasePipeline):
    nombre = 'automatizador_inteligente_308'
    descripcion = 'Prepara y ejecuta acciones conversacionales con confirmación y trazabilidad.'
    acciones_soportadas = ['preparar', 'ejecutar', 'validar_confirmacion']

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros or {}
        svc = self.core.automatizador_inteligente_308
        if solicitud.accion == 'preparar':
            d = svc.preparar(p.get('texto',''), p.get('analisis'), p.get('seleccion'), p.get('contexto'))
        elif solicitud.accion == 'ejecutar':
            d = svc.ejecutar(p.get('texto',''), p.get('confirmado', False), p.get('analisis'), p.get('seleccion'), p.get('contexto'))
        elif solicitud.accion == 'validar_confirmacion':
            d = svc.validar_confirmacion(p.get('plan', {}), p.get('confirmado', False))
        else:
            return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
        return ResultadoPipeline(True, self.nombre, solicitud.accion, d.get('lectura_host_ai','Automatización procesada.'), d, d.get('riesgos', []), bool(d.get('requiere_confirmacion', False)))
