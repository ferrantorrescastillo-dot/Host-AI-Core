from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineBaseActualizacionPreciosFactura(BasePipeline):
    nombre = "base_actualizacion_precios_factura"
    descripcion = "Base para preparar actualizaciones de precios desde facturas."
    acciones_soportadas = ["preparar_cambio", "preparar_informe", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "preparar_cambio":
            d = self.core.base_actualizacion_precios_factura.preparar_cambio(p["relacion"], p.get("precio_anterior", 0.0))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], d.get("requiere_revision", False))
        if solicitud.accion == "preparar_informe":
            d = self.core.base_actualizacion_precios_factura.preparar_informe(p["informe_relaciones"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, ["Revisar cambios marcados."], d.get("requieren_revision", 0) > 0)
        if solicitud.accion == "exportar":
            d = self.core.base_actualizacion_precios_factura.exportar_informe(p["informe"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
