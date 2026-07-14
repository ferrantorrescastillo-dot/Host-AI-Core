from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineCierreGestionInteligenteStock(BasePipeline):
    nombre = 'cierre_gestion_inteligente_stock'
    descripcion = 'Cierra y valida el bloque 3.0.5 Gestión Inteligente del Stock como sistema único.'
    acciones_soportadas = ['cerrar', 'exportar']
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == 'cerrar':
            d = self.core.cierre_gestion_inteligente_stock.generar_cierre(p.get('horizonte_dias', 14))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        if solicitud.accion == 'exportar':
            d = self.core.cierre_gestion_inteligente_stock.exportar_cierre(p['cierre'], p.get('nombre',''))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d['lectura_host_ai'], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, 'Acción no implementada.', errores=[f'Acción no implementada: {solicitud.accion}'])
