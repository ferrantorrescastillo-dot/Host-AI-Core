from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineReconciliadorInteligenteStock(BasePipeline):
    nombre = "reconciliador_inteligente_stock"
    descripcion = "Reconcile stock teórico, inventario físico, movimientos, compras y producción."
    acciones_soportadas = ["reconciliar", "exportar"]
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "reconciliar":
            d = self.core.reconciliador_inteligente_stock.reconciliar_stock(p.get("inventario_fisico"), p.get("tolerancia", 0.01))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "exportar":
            d = self.core.reconciliador_inteligente_stock.exportar_reconciliacion(p["informe"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
