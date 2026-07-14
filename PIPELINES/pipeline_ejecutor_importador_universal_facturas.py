from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineEjecutorImportadorUniversalFacturas(BasePipeline):
    nombre = "ejecutor_importador_universal_facturas"
    descripcion = "Ejecuta importaciones universales de facturas aplicando precios y stock."
    acciones_soportadas = ["ejecutar_archivo", "ejecutar_preparacion", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "ejecutar_archivo":
            d = self.core.ejecutor_importador_universal_facturas.ejecutar_desde_archivo(
                p["ruta_archivo"],
                texto_manual_ocr=p.get("texto_manual_ocr", ""),
                forzar=p.get("forzar", False),
            )
            return ResultadoPipeline(d.get("ok", False), self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], not d.get("aplicado", False))
        if solicitud.accion == "ejecutar_preparacion":
            d = self.core.ejecutor_importador_universal_facturas.ejecutar_preparacion(
                p["preparacion"],
                forzar=p.get("forzar", False),
            )
            return ResultadoPipeline(d.get("ok", False), self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], not d.get("aplicado", False))
        if solicitud.accion == "exportar":
            d = self.core.ejecutor_importador_universal_facturas.exportar_resultado(p["resultado"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
