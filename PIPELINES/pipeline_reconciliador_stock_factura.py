from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineReconciliadorStockFactura(BasePipeline):
    nombre = "reconciliador_stock_factura"
    descripcion = "Reconciliación entre factura y entradas de stock aplicadas."
    acciones_soportadas = ["reconciliar_movimiento", "reconciliar_informe", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "reconciliar_movimiento":
            d = self.core.reconciliador_stock_factura.reconciliar_movimiento(p["movimiento"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], d.get("estado") != "correcto")
        if solicitud.accion == "reconciliar_informe":
            d = self.core.reconciliador_stock_factura.reconciliar_informe(p["informe_stock"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], not d.get("puede_cerrar_factura", False))
        if solicitud.accion == "exportar":
            d = self.core.reconciliador_stock_factura.exportar_informe(p["informe"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
