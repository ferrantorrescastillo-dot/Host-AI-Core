from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineCierreImportadorUniversal(BasePipeline):
    nombre = "cierre_importador_universal"
    descripcion = "Comprueba y cierra el bloque Importador Universal."
    acciones_soportadas = ["comprobar", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "comprobar":
            d = self.core.cierre_importador_universal.comprobar_cierre()
            return ResultadoPipeline(d.get("listo_para_uso", False), self.nombre, solicitud.accion, d["lectura_host_ai"], d, d.get("recomendaciones", []), not d.get("listo_para_uso", False))
        if solicitud.accion == "exportar":
            d = self.core.cierre_importador_universal.exportar_informe(p["informe"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
