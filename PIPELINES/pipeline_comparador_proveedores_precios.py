from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineComparadorProveedoresPrecios(BasePipeline):
    nombre = "comparador_proveedores_precios"
    descripcion = "Compara proveedores usando histórico de precios."
    acciones_soportadas = ["comparar_articulo", "comparar_todos", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "comparar_articulo":
            d = self.core.comparador_proveedores_precios.comparar_articulo(p["articulo_id"])
            return ResultadoPipeline(d.get("encontrado", False), self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], not d.get("encontrado", False))
        if solicitud.accion == "comparar_todos":
            d = self.core.comparador_proveedores_precios.comparar_todos()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "exportar":
            d = self.core.comparador_proveedores_precios.exportar_comparacion(p["comparacion"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
