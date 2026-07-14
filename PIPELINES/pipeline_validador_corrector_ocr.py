from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineValidadorCorrectorOCR(BasePipeline):
    nombre = "validador_corrector_ocr"
    descripcion = "Valida y corrige texto OCR antes de leer facturas."
    acciones_soportadas = ["validar_texto", "validar_resultado_ocr", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "validar_texto":
            d = self.core.validador_corrector_ocr.validar_y_corregir_texto(p["texto"])
            return ResultadoPipeline(d["valido"], self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], not d["valido"])
        if solicitud.accion == "validar_resultado_ocr":
            d = self.core.validador_corrector_ocr.validar_resultado_ocr(p["resultado_ocr"])
            return ResultadoPipeline(d["valido"], self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], not d["valido"])
        if solicitud.accion == "exportar":
            d = self.core.validador_corrector_ocr.exportar_validacion(p["validacion"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
