from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineAnalizadorInteligenteEscandallos(BasePipeline):
    nombre='analizador_inteligente_escandallos'
    descripcion='Analiza escandallos, costes, mermas, raciones, margen, rentabilidad y costes ocultos.'
    acciones_soportadas=['analizar','exportar']
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p=solicitud.parametros
        if solicitud.accion=='analizar':
            d=self.core.analizador_inteligente_escandallos.analizar_escandallos(p.get('escandallos'), p.get('coste_hora_cocinero',18.0), p.get('pct_costes_ocultos',4.0))
            return ResultadoPipeline(True,self.nombre,solicitud.accion,d['lectura_host_ai'],d,[],False)
        if solicitud.accion=='exportar':
            d=self.core.analizador_inteligente_escandallos.exportar_analisis(p['analisis'], p.get('nombre',''))
            return ResultadoPipeline(True,self.nombre,solicitud.accion,d['lectura_host_ai'],d,[],False)
        return ResultadoPipeline(False,self.nombre,solicitud.accion,'Acción no implementada.',errores=[f'Acción no implementada: {solicitud.accion}'])
