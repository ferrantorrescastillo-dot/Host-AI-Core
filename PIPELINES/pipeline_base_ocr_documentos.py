from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineBaseOCRDocumentos(BasePipeline):
    nombre = "base_ocr_documentos"
    descripcion = "Diagnóstico OCR para PDFs e imágenes escaneadas."
    acciones_soportadas = ["diagnosticar_archivo", "diagnosticar_lote", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "diagnosticar_archivo":
            d = self.core.base_ocr_documentos.diagnosticar_archivo(p["ruta_archivo"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], d.get("necesita_ocr", False))
        if solicitud.accion == "diagnosticar_lote":
            d = self.core.base_ocr_documentos.diagnosticar_lote(p["rutas"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], d.get("necesitan_ocr", 0) > 0)
        if solicitud.accion == "exportar":
            d = self.core.base_ocr_documentos.exportar_diagnostico(p["diagnostico"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
