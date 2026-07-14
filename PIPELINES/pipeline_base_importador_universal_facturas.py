from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineBaseImportadorUniversalFacturas(BasePipeline):
    nombre = "base_importador_universal_facturas"
    descripcion = "Base del importador universal de facturas."
    acciones_soportadas = ["planificar", "preparar", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "planificar":
            d = self.core.base_importador_universal_facturas.planificar_importacion(p["ruta_archivo"])
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], d.get("requiere_revision", False))
        if solicitud.accion == "preparar":
            d = self.core.base_importador_universal_facturas.preparar_importacion(
                p["ruta_archivo"],
                texto_manual_ocr=p.get("texto_manual_ocr", ""),
            )
            return ResultadoPipeline(d.get("ok", False), self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], d.get("requiere_revision", True))
        if solicitud.accion == "exportar":
            d = self.core.base_importador_universal_facturas.exportar_preparacion(p["resultado"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
