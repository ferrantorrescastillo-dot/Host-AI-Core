from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineMotorOCRSimulado(BasePipeline):
    nombre = "motor_ocr_simulado"
    descripcion = "Motor OCR simulado con texto manual para documentos escaneados."
    acciones_soportadas = ["registrar_texto_manual", "extraer_texto", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "registrar_texto_manual":
            d = self.core.motor_ocr_simulado.registrar_texto_manual(p["ruta_archivo"], p["texto"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "extraer_texto":
            d = self.core.motor_ocr_simulado.extraer_texto(p["ruta_archivo"], p.get("texto_manual", ""))
            return ResultadoPipeline(bool(d.get("texto_extraido")), self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], d.get("requiere_revision", True))
        if solicitud.accion == "exportar":
            d = self.core.motor_ocr_simulado.exportar_resultado(p["resultado"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
