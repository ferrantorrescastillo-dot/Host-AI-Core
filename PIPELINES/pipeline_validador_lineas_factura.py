from __future__ import annotations

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineValidadorLineasFactura(BasePipeline):
    nombre = "validador_lineas_factura"
    descripcion = "Validador inteligente de líneas de factura."
    acciones_soportadas = ["validar_linea", "validar_factura", "validar_texto", "validar_pdf", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "validar_linea":
            datos = self.core.validador_lineas_factura.validar_linea(p["linea"])
            return ResultadoPipeline(datos.get("valida", False), self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], not datos.get("valida", False))

        if solicitud.accion == "validar_factura":
            datos = self.core.validador_lineas_factura.validar_factura_completa(p["bloque"])
            return ResultadoPipeline(datos.get("puede_importar", False), self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, ["Revisar avisos antes de importar."], not datos.get("puede_importar", False))

        if solicitud.accion == "validar_texto":
            datos = self.core.validador_lineas_factura.validar_factura_desde_texto(
                texto=p["texto"],
                proveedor_sugerido=p.get("proveedor_sugerido", ""),
                cif_sugerido=p.get("cif_sugerido", ""),
                numero_factura=p.get("numero_factura", ""),
                fecha_factura=p.get("fecha_factura", ""),
                total_factura_detectado=p.get("total_factura_detectado", 0.0),
            )
            return ResultadoPipeline(datos.get("puede_importar", False), self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, ["Revisar avisos antes de importar."], not datos.get("puede_importar", False))

        if solicitud.accion == "validar_pdf":
            datos = self.core.validador_lineas_factura.validar_factura_desde_pdf(p["ruta_archivo"])
            return ResultadoPipeline(datos.get("puede_importar", False), self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, ["Revisar avisos antes de importar."], not datos.get("puede_importar", False))

        if solicitud.accion == "exportar":
            datos = self.core.validador_lineas_factura.exportar_validacion(p["informe"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
