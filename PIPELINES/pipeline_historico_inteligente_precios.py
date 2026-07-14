from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineHistoricoInteligentePrecios(BasePipeline):
    nombre = "historico_inteligente_precios"
    descripcion = "Histórico y análisis de precios por artículo."
    acciones_soportadas = ["registrar", "registrar_desde_aplicacion", "analizar_articulo", "listar", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "registrar":
            d = self.core.historico_inteligente_precios.registrar_precio(p["registro"])
            return ResultadoPipeline(d.get("registrado", False), self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], not d.get("registrado", False))
        if solicitud.accion == "registrar_desde_aplicacion":
            d = self.core.historico_inteligente_precios.registrar_desde_aplicacion(p["resultado_aplicacion"])
            return ResultadoPipeline(d.get("registrado", False), self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], not d.get("registrado", False))
        if solicitud.accion == "analizar_articulo":
            d = self.core.historico_inteligente_precios.analizar_articulo(p["articulo_id"])
            return ResultadoPipeline(d.get("encontrado", False), self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], not d.get("encontrado", False))
        if solicitud.accion == "listar":
            d = self.core.historico_inteligente_precios.listar_historico()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "exportar":
            d = self.core.historico_inteligente_precios.exportar()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
