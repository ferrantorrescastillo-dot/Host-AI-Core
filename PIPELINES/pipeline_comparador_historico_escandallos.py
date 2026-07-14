from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineComparadorHistoricoEscandallos(BasePipeline):
    nombre='comparador_historico_escandallos'
    descripcion='Compara históricamente escandallos: coste, margen, ingredientes, proveedores y evolución económica.'
    acciones_soportadas=['comparar','exportar']
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p=solicitud.parametros
        if solicitud.accion=='comparar':
            d=self.core.comparador_historico_escandallos.comparar_historico(p.get('escandallos_anteriores'), p.get('escandallos_actuales'), p.get('analisis_anterior'), p.get('analisis_actual'))
            return ResultadoPipeline(True,self.nombre,solicitud.accion,d['lectura_host_ai'],d,[],False)
        if solicitud.accion=='exportar':
            d=self.core.comparador_historico_escandallos.exportar_comparativa(p['comparativa'], p.get('nombre',''))
            return ResultadoPipeline(True,self.nombre,solicitud.accion,d['lectura_host_ai'],d,[],False)
        return ResultadoPipeline(False,self.nombre,solicitud.accion,'Acción no implementada.',errores=[f'Acción no implementada: {solicitud.accion}'])
