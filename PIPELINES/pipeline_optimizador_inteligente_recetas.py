from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineOptimizadorInteligenteRecetas(BasePipeline):
    nombre='optimizador_inteligente_recetas'
    descripcion='Optimiza recetas y escandallos: sustituciones, reducción de coste, mejora de margen, mermas y cantidades.'
    acciones_soportadas=['optimizar','exportar']
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p=solicitud.parametros
        if solicitud.accion=='optimizar':
            d=self.core.optimizador_inteligente_recetas.optimizar_recetas(p.get('escandallos'), p.get('analisis'), p.get('objetivo_food_cost_pct',30.0), p.get('margen_minimo_pct',25.0))
            return ResultadoPipeline(True,self.nombre,solicitud.accion,d['lectura_host_ai'],d,[],False)
        if solicitud.accion=='exportar':
            d=self.core.optimizador_inteligente_recetas.exportar_optimizacion(p['optimizacion'], p.get('nombre',''))
            return ResultadoPipeline(True,self.nombre,solicitud.accion,d['lectura_host_ai'],d,[],False)
        return ResultadoPipeline(False,self.nombre,solicitud.accion,'Acción no implementada.',errores=[f'Acción no implementada: {solicitud.accion}'])
