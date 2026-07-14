from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineCierreEscandallosInteligentes(BasePipeline):
    nombre = 'cierre_escandallos_inteligentes'
    descripcion = 'Cierra y valida el bloque completo Host AI 3.0.7 Escandallos Inteligentes.'
    acciones_soportadas = ['comprobar', 'exportar']

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == 'comprobar':
            d = self.core.cierre_escandallos_inteligentes.comprobar_cierre(p.get('escandallos'), p.get('historico'), p.get('ventas'), p.get('objetivos'))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, d.get('acciones_recomendadas', []), False)
        if solicitud.accion == 'exportar':
            d = self.core.cierre_escandallos_inteligentes.exportar_cierre(p['cierre'], p.get('nombre', ''))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
