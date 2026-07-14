from __future__ import annotations

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineParserLineasFactura(BasePipeline):
    nombre = "parser_lineas_factura"
    descripcion = "Parser inicial de líneas de factura desde texto/PDF."
    acciones_soportadas = ["leer_texto", "leer_pdf", "exportar_lineas"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "leer_texto":
            datos = self.core.parser_lineas_factura.leer_lineas_desde_texto(
                texto=p["texto"],
                proveedor_id=p.get("proveedor_id", ""),
                proveedor_nombre=p.get("proveedor_nombre", ""),
                numero_factura=p.get("numero_factura", ""),
                fecha_factura=p.get("fecha_factura", ""),
                total_factura_detectado=p.get("total_factura_detectado", 0.0),
            )
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        if solicitud.accion == "leer_pdf":
            datos = self.core.parser_lineas_factura.leer_lineas_desde_pdf(
                ruta_archivo=p["ruta_archivo"],
                lector_pdf_facturas=self.core.lector_pdf_facturas,
                detector_proveedores_pdf=getattr(self.core, "detector_proveedores_pdf", None),
            )
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        if solicitud.accion == "exportar_lineas":
            datos = self.core.parser_lineas_factura.exportar_lineas(p["bloque"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
