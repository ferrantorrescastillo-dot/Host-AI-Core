from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineCierreIAConversacional308(BasePipeline):
    nombre = 'cierre_ia_conversacional_308'
    descripcion = 'Cierre final del bloque Host AI 3.0.8 IA Conversacional.'
    acciones_soportadas = ['comprobar', 'exportar']

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros or {}
        svc = self.core.cierre_ia_conversacional_308
        if solicitud.accion == 'comprobar':
            d = svc.comprobar(p.get('ejecutar_pruebas', True))
        elif solicitud.accion == 'exportar':
            d = svc.exportar(p.get('nombre',''))
        else:
            return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
        return ResultadoPipeline(bool(d.get('ok_global', True)), self.nombre, solicitud.accion, d.get('lectura_host_ai','Cierre IA Conversacional procesado.'), d, d.get('acciones_recomendadas', []), False, d.get('incidencias', []))
