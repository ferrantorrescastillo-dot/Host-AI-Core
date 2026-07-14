from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineActualizadorInteligenteStockFactura(BasePipeline):
    nombre = "actualizador_inteligente_stock_factura"
    descripcion = "Aplica entradas de stock desde facturas."
    acciones_soportadas = ["aplicar_movimiento", "aplicar_informe", "preparar_y_aplicar", "stock_articulo", "listar_log", "exportar_log"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "aplicar_movimiento":
            d = self.core.actualizador_inteligente_stock_factura.aplicar_movimiento(p["movimiento"], p.get("forzar", False))
            return ResultadoPipeline(d["aplicado"], self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], not d["aplicado"])
        if solicitud.accion == "aplicar_informe":
            d = self.core.actualizador_inteligente_stock_factura.aplicar_informe(p["informe"], p.get("forzar", False))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], d.get("bloqueados", 0) > 0)
        if solicitud.accion == "preparar_y_aplicar":
            d = self.core.actualizador_inteligente_stock_factura.preparar_y_aplicar(p["informe_relaciones"], p.get("forzar", False))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], d.get("bloqueados", 0) > 0)
        if solicitud.accion == "stock_articulo":
            d = self.core.actualizador_inteligente_stock_factura.stock_actual_articulo(p["articulo_id"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "listar_log":
            d = self.core.actualizador_inteligente_stock_factura.listar_log()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "exportar_log":
            d = self.core.actualizador_inteligente_stock_factura.exportar_log()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
