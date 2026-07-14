from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineValidadorRelacionesArticulosFactura(BasePipeline):
    nombre = "validador_relaciones_articulos_factura"
    descripcion = "Valida relaciones entre líneas de factura y artículos internos."
    acciones_soportadas = ["validar_relacion", "validar_informe", "validar_texto", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "validar_relacion":
            d = self.core.validador_relaciones_articulos_factura.validar_relacion(p["relacion"])
            return ResultadoPipeline(d["valida"], self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], not d["valida"])
        if solicitud.accion == "validar_informe":
            d = self.core.validador_relaciones_articulos_factura.validar_informe(p["informe"])
            return ResultadoPipeline(d["puede_continuar"], self.nombre, solicitud.accion, d["lectura_host_ai"], d, ["Revisar relaciones pendientes."], not d["puede_continuar"])
        if solicitud.accion == "validar_texto":
            d = self.core.validador_relaciones_articulos_factura.validar_factura_texto(
                texto=p["texto"],
                proveedor_sugerido=p.get("proveedor_sugerido", ""),
                cif_sugerido=p.get("cif_sugerido", ""),
                numero_factura=p.get("numero_factura", ""),
                fecha_factura=p.get("fecha_factura", ""),
                total_factura_detectado=p.get("total_factura_detectado", 0.0),
            )
            return ResultadoPipeline(d["puede_continuar"], self.nombre, solicitud.accion, d["lectura_host_ai"], d, ["Revisar relaciones pendientes."], not d["puede_continuar"])
        if solicitud.accion == "exportar":
            d = self.core.validador_relaciones_articulos_factura.exportar_validacion(p["informe"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
