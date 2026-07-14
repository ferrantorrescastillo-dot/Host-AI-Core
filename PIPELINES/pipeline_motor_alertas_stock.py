from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineMotorAlertasStock(BasePipeline):
    nombre = "motor_alertas_stock"
    descripcion = "Genera alertas inteligentes de stock bajo, rotura, exceso, caducidad, producto parado y sin ubicación."
    acciones_soportadas = ["generar", "exportar"]
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "generar":
            d = self.core.motor_alertas_stock.generar_alertas(p.get("dias_caducidad_alerta", 3), p.get("dias_sin_movimiento", 30))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [a.get("accion_recomendada", "") for a in d.get("alertas", []) if a.get("accion_recomendada")], d.get("criticas", 0) > 0)
        if solicitud.accion == "exportar":
            d = self.core.motor_alertas_stock.exportar_alertas(p["alertas"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
