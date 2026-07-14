from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelinePrediccionNecesidadesStock(BasePipeline):
    nombre = "prediccion_necesidades_stock"
    descripcion = "Predice necesidades futuras de stock cruzando consumo, compras, producción y eventos."
    acciones_soportadas = ["predecir", "exportar"]
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "predecir":
            d = self.core.prediccion_necesidades_stock.predecir_necesidades(p.get("horizonte_dias", 14), p.get("produccion_prevista"), p.get("eventos_previstos"))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "exportar":
            d = self.core.prediccion_necesidades_stock.exportar_prediccion(p["prediccion"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
