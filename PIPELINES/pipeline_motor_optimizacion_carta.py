from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineMotorOptimizacionCarta(BasePipeline):
    nombre = 'motor_optimizacion_carta'
    descripcion = 'Optimiza carta completa por rentabilidad, demanda, food cost, complejidad y riesgo.'
    acciones_soportadas = ['optimizar', 'exportar']

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == 'optimizar':
            d = self.core.motor_optimizacion_carta.optimizar_carta(p.get('escandallos'), p.get('analisis'), p.get('prediccion'), p.get('ventas'), p.get('objetivos'))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        if solicitud.accion == 'exportar':
            d = self.core.motor_optimizacion_carta.exportar_optimizacion(p['optimizacion'], p.get('nombre', ''))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
