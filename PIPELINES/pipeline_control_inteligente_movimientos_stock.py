from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineControlInteligenteMovimientosStock(BasePipeline):
    nombre = "control_inteligente_movimientos_stock"
    descripcion = "Controla entradas, salidas, ajustes, mermas, pérdidas y descuadres de stock."
    acciones_soportadas = ["analizar", "exportar"]
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "analizar":
            d = self.core.control_inteligente_movimientos_stock.analizar_movimientos()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "exportar":
            d = self.core.control_inteligente_movimientos_stock.exportar_movimientos(p["informe"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
