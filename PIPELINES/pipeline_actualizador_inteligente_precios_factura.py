from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineActualizadorInteligentePreciosFactura(BasePipeline):
    nombre = "actualizador_inteligente_precios_factura"
    descripcion = "Aplica actualizaciones de precios desde facturas."
    acciones_soportadas = ["aplicar_cambio", "aplicar_informe", "preparar_y_aplicar", "listar_log", "exportar_log"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "aplicar_cambio":
            d = self.core.actualizador_inteligente_precios_factura.aplicar_cambio(p["cambio"], p.get("forzar", False))
            return ResultadoPipeline(d["aplicado"], self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], not d["aplicado"])
        if solicitud.accion == "aplicar_informe":
            d = self.core.actualizador_inteligente_precios_factura.aplicar_informe(p["informe"], p.get("forzar", False))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], d.get("bloqueados", 0) > 0)
        if solicitud.accion == "preparar_y_aplicar":
            d = self.core.actualizador_inteligente_precios_factura.preparar_y_aplicar(p["informe_relaciones"], p.get("forzar", False))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], d.get("bloqueados", 0) > 0)
        if solicitud.accion == "listar_log":
            d = self.core.actualizador_inteligente_precios_factura.listar_log()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "exportar_log":
            d = self.core.actualizador_inteligente_precios_factura.exportar_log()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
