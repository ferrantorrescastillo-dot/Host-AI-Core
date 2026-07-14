from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineMemoriaConversacional308(BasePipeline):
    nombre = 'memoria_conversacional_308'
    descripcion = 'Memoria conversacional persistente para contexto, referencias y continuidad operativa.'
    acciones_soportadas = ['recordar', 'consultar', 'resolver_referencias', 'aprender_desde_turno', 'limpiar', 'exportar']

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros or {}
        svc = self.core.memoria_conversacional_308
        if solicitud.accion == 'recordar':
            d = svc.recordar(p.get('clave',''), p.get('valor'), p.get('tipo','contexto'), p.get('prioridad',1), p.get('origen','usuario'), p.get('tags'), p.get('metadatos'))
        elif solicitud.accion == 'consultar':
            d = svc.consultar(p.get('clave',''), p.get('filtro_tipo',''), p.get('tags'))
        elif solicitud.accion == 'resolver_referencias':
            d = svc.resolver_referencias(p.get('texto',''), p.get('contexto'))
        elif solicitud.accion == 'aprender_desde_turno':
            d = svc.aprender_desde_turno(p.get('turno', {}))
        elif solicitud.accion == 'limpiar':
            d = svc.limpiar()
        elif solicitud.accion == 'exportar':
            d = svc.exportar(p.get('nombre',''))
        else:
            return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
        return ResultadoPipeline(True, self.nombre, solicitud.accion, d.get('lectura_host_ai','Memoria conversacional procesada.'), d, [], False)
