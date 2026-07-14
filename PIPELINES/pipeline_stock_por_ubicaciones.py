from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineStockPorUbicaciones(BasePipeline):
    nombre = 'stock_por_ubicaciones'
    descripcion = 'Analiza y mueve stock por ubicaciones operativas: cámara, congelador, seco, producción, evento y almacén externo.'
    acciones_soportadas = ['analizar', 'mover', 'exportar']
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == 'analizar':
            d = self.core.stock_por_ubicaciones.analizar_ubicaciones()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        if solicitud.accion == 'mover':
            d = self.core.stock_por_ubicaciones.mover_stock(p['nombre'], p['cantidad'], p['unidad'], p.get('origen',''), p.get('destino',''), p.get('articulo_id',''), p.get('lote_id',''))
            return ResultadoPipeline(bool(d.get('ok', True)), self.nombre, solicitud.accion, d.get('mensaje','Movimiento procesado.'), d, [] if d.get('ok', True) else [d.get('mensaje','Error moviendo stock.')], False)
        if solicitud.accion == 'exportar':
            d = self.core.stock_por_ubicaciones.exportar_ubicaciones(p['informe'], p.get('nombre',''))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
