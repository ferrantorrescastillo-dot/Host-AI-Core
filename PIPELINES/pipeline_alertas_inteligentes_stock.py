from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineAlertasInteligentesStock(BasePipeline):
    nombre = "alertas_inteligentes_stock"
    descripcion = "Genera alertas inteligentes de stock bajo, sin stock o exceso."
    acciones_soportadas = ["generar_articulo", "generar_todos", "listar", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "generar_articulo":
            d = self.core.alertas_inteligentes_stock.generar_alertas_articulo(
                p["articulo_id"],
                stock_minimo=p.get("stock_minimo", None),
                stock_exceso=p.get("stock_exceso", None),
            )
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], d.get("total", 0) > 0)
        if solicitud.accion == "generar_todos":
            d = self.core.alertas_inteligentes_stock.generar_alertas_todos(
                stock_minimo=p.get("stock_minimo", None),
                stock_exceso=p.get("stock_exceso", None),
            )
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], d.get("total", 0) > 0)
        if solicitud.accion == "listar":
            d = self.core.alertas_inteligentes_stock.listar_alertas()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "exportar":
            d = self.core.alertas_inteligentes_stock.exportar_alertas()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
