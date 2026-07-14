from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineLectorFacturasConOCR(BasePipeline):
    nombre = "lector_facturas_con_ocr"
    descripcion = "Integra OCR simulado con lectura completa de facturas."
    acciones_soportadas = ["leer_archivo", "validar_y_relacionar", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "leer_archivo":
            d = self.core.lector_facturas_con_ocr.leer_archivo_con_ocr(
                p["ruta_archivo"],
                texto_manual=p.get("texto_manual", ""),
                exportar_json=p.get("exportar_json", True),
            )
            return ResultadoPipeline(d.get("ok", True), self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], not d.get("ok", True))
        if solicitud.accion == "validar_y_relacionar":
            d = self.core.lector_facturas_con_ocr.validar_y_relacionar_archivo_ocr(
                p["ruta_archivo"],
                texto_manual=p.get("texto_manual", ""),
            )
            return ResultadoPipeline(d.get("ok", True), self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], not d.get("ok", True))
        if solicitud.accion == "exportar":
            d = self.core.lector_facturas_con_ocr.exportar_lectura(p["lectura"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
