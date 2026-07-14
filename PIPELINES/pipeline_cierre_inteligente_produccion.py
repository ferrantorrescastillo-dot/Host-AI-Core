from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineCierreInteligenteProduccion(BasePipeline):
    nombre = 'cierre_inteligente_produccion'
    descripcion = 'Cierra y valida el bloque completo Host AI 3.0.6 Producción.'
    acciones_soportadas = ['comprobar', 'exportar']
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == 'comprobar':
            d = self.core.cierre_inteligente_produccion.comprobar_cierre(p.get('elaboraciones'), p.get('analisis'), p.get('alertas'), p.get('planificacion'), p.get('asignacion'), p.get('control'), p.get('replanificacion'), p.get('optimizacion'))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        if solicitud.accion == 'exportar':
            d = self.core.cierre_inteligente_produccion.exportar_cierre(p['cierre'], p.get('nombre',''))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
