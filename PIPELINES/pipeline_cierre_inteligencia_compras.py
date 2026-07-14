from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineCierreInteligenciaCompras(BasePipeline):
    nombre = "cierre_inteligencia_compras"
    descripcion = "Cierra el bloque Host AI 3.0.4 validando todos los módulos de Inteligencia de Compras."
    acciones_soportadas = ["comprobar", "exportar"]
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "comprobar":
            d = self.core.cierre_inteligencia_compras.comprobar_cierre()
            return ResultadoPipeline(bool(d.get("ok_global")), self.nombre, solicitud.accion, d["lectura_host_ai"], d, d.get("acciones_recomendadas", []), False)
        if solicitud.accion == "exportar":
            d = self.core.cierre_inteligencia_compras.exportar_cierre(p["cierre"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])
