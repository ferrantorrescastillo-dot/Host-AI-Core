from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineComparadorInteligenteProveedores(BasePipeline):
    nombre = "comparador_inteligente_proveedores"
    descripcion = "Compara proveedores por precio, estabilidad, frecuencia, incidencias y calidad histórica."
    acciones_soportadas = ["comparar", "comparar_articulo", "exportar"]
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "comparar":
            d = self.core.comparador_inteligente_proveedores.comparar_proveedores()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "comparar_articulo":
            d = self.core.comparador_inteligente_proveedores.comparar_articulo(p["articulo_id"])
            return ResultadoPipeline(bool(d.get("encontrado")), self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "exportar":
            d = self.core.comparador_inteligente_proveedores.exportar_comparacion(p["comparacion"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
