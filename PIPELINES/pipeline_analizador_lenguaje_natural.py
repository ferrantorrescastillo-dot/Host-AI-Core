from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineAnalizadorLenguajeNatural(BasePipeline):
    nombre = 'analizador_lenguaje_natural'
    descripcion = 'Analiza lenguaje natural y lo convierte en intención, entidades y solicitud estructurada Host AI.'
    acciones_soportadas = ['analizar', 'exportar']

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros or {}
        if solicitud.accion == 'analizar':
            d = self.core.analizador_lenguaje_natural.analizar(p.get('texto',''), p.get('contexto'))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        if solicitud.accion == 'exportar':
            d = self.core.analizador_lenguaje_natural.exportar_analisis(p['analisis'], p.get('nombre',''))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
