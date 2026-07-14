from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineSimuladorCostesEscandallos(BasePipeline):
    nombre='simulador_costes_escandallos'
    descripcion='Simula cambios de proveedor, precios, gramajes, mermas y precio de venta en escandallos.'
    acciones_soportadas=['simular','exportar']
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p=solicitud.parametros
        if solicitud.accion=='simular':
            d=self.core.simulador_costes_escandallos.simular_costes(p.get('escandallos'), p.get('analisis'), p.get('escenarios'))
            return ResultadoPipeline(True,self.nombre,solicitud.accion,d['lectura_host_ai'],d,[],False)
        if solicitud.accion=='exportar':
            d=self.core.simulador_costes_escandallos.exportar_simulacion(p['simulacion'], p.get('nombre',''))
            return ResultadoPipeline(True,self.nombre,solicitud.accion,d['lectura_host_ai'],d,[],False)
        return ResultadoPipeline(False,self.nombre,solicitud.accion,'Acción no implementada.',errores=[f'Acción no implementada: {solicitud.accion}'])
