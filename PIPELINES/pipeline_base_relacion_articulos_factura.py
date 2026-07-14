from __future__ import annotations

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineBaseRelacionArticulosFactura(BasePipeline):
    nombre = "base_relacion_articulos_factura"
    descripcion = "Modelos base para relacionar líneas de factura con artículos internos."
    acciones_soportadas = ["crear_relacion_demo", "crear_informe_demo", "validar_informe", "exportar_informe"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "crear_relacion_demo":
            datos = self.core.base_relacion_articulos_factura.crear_relacion_demo()
            datos["lectura_host_ai"] = "Relación demo creada."
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        if solicitud.accion == "crear_informe_demo":
            datos = self.core.base_relacion_articulos_factura.crear_informe_demo()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        if solicitud.accion == "validar_informe":
            datos = self.core.base_relacion_articulos_factura.validar_informe(p["informe"])
            return ResultadoPipeline(datos["ok"], self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], not datos["ok"])

        if solicitud.accion == "exportar_informe":
            datos = self.core.base_relacion_articulos_factura.exportar_informe(p["informe"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
