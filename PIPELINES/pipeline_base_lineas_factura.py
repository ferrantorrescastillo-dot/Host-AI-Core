from __future__ import annotations

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineBaseLineasFactura(BasePipeline):
    nombre = "base_lineas_factura"
    descripcion = "Modelos y utilidades base para líneas de factura."
    acciones_soportadas = ["crear_linea_demo", "crear_bloque_demo", "validar_bloque", "exportar_bloque"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "crear_linea_demo":
            datos = self.core.base_lineas_factura.crear_linea_demo()
            datos["lectura_host_ai"] = "Línea de factura demo creada."
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        if solicitud.accion == "crear_bloque_demo":
            datos = self.core.base_lineas_factura.crear_bloque_demo()
            datos["lectura_host_ai"] = "Bloque de líneas demo creado."
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        if solicitud.accion == "validar_bloque":
            datos = self.core.base_lineas_factura.validar_bloque(p["bloque"])
            return ResultadoPipeline(datos["ok"], self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], not datos["ok"])

        if solicitud.accion == "exportar_bloque":
            datos = self.core.base_lineas_factura.exportar_bloque(p["bloque"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
