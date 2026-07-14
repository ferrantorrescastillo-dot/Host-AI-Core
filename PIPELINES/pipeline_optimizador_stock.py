from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineOptimizadorStock(BasePipeline):
    nombre = "optimizador_stock"
    descripcion = "Genera acciones para comprar, no comprar, reducir, consumir antes y corregir problemas de stock."
    acciones_soportadas = ["optimizar", "exportar"]
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "optimizar":
            d = self.core.optimizador_stock.optimizar_stock(p.get("horizonte_dias", 14))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "exportar":
            d = self.core.optimizador_stock.exportar_optimizacion(p["optimizacion"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
