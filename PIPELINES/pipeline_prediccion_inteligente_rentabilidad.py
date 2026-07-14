from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelinePrediccionInteligenteRentabilidad(BasePipeline):
    nombre='prediccion_inteligente_rentabilidad'
    descripcion='Predice margen y beneficio esperado conectando escandallos, histórico, compras, stock y tendencia.'
    acciones_soportadas=['predecir','exportar']
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p=solicitud.parametros
        if solicitud.accion=='predecir':
            d=self.core.prediccion_inteligente_rentabilidad.predecir_rentabilidad(p.get('escandallos'), p.get('analisis'), p.get('historico'), p.get('horizonte_meses',3))
            return ResultadoPipeline(True,self.nombre,solicitud.accion,d['lectura_host_ai'],d,[],False)
        if solicitud.accion=='exportar':
            d=self.core.prediccion_inteligente_rentabilidad.exportar_prediccion(p['prediccion'], p.get('nombre',''))
            return ResultadoPipeline(True,self.nombre,solicitud.accion,d['lectura_host_ai'],d,[],False)
        return ResultadoPipeline(False,self.nombre,solicitud.accion,'Acción no implementada.',errores=[f'Acción no implementada: {solicitud.accion}'])
