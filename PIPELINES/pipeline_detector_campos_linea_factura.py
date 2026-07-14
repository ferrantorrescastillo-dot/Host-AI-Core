from __future__ import annotations

from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineDetectorCamposLineaFactura(BasePipeline):
    nombre = "detector_campos_linea_factura"
    descripcion = "Detector de cantidades, unidades, precios e importes en líneas de factura."
    acciones_soportadas = ["detectar_linea", "detectar_lote", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros

        if solicitud.accion == "detectar_linea":
            datos = self.core.detector_campos_linea_factura.detectar_campos(p["linea"])
            return ResultadoPipeline(datos.get("ok", False), self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], not datos.get("ok", False))

        if solicitud.accion == "detectar_lote":
            datos = self.core.detector_campos_linea_factura.detectar_lote(p["lineas"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        if solicitud.accion == "exportar":
            datos = self.core.detector_campos_linea_factura.exportar_resultados(p["resultados"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, datos["lectura_host_ai"], datos, [], False)

        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
