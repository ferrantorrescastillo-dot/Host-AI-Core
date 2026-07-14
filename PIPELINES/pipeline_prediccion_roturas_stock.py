from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelinePrediccionRoturasStock(BasePipeline):
    nombre = "prediccion_roturas_stock"
    descripcion = "Predice roturas de stock usando consumo, compras y movimientos históricos."
    acciones_soportadas = ["predecir", "predecir_articulo", "exportar"]
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "predecir":
            d = self.core.prediccion_roturas_stock.predecir_roturas(p.get("horizonte_dias", 14))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "predecir_articulo":
            d = self.core.prediccion_roturas_stock.predecir_articulo(p["articulo_id"], p.get("horizonte_dias", 14))
            return ResultadoPipeline(bool(d.get("encontrado")), self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "exportar":
            d = self.core.prediccion_roturas_stock.exportar_prediccion(p["prediccion"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
