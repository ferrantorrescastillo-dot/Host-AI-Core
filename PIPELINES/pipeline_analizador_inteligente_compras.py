"""Pipeline del analizador inteligente de compras.

RC2.8: documentación interna y contrato público sin cambiar comportamiento."""

from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineAnalizadorInteligenteCompras(BasePipeline):
    nombre = "analizador_inteligente_compras"
    descripcion = "Analiza importaciones, compras, precios y stock."
    acciones_soportadas = ["analizar", "exportar"]

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "analizar":
            d = self.core.analizador_inteligente_compras.analizar_compras()
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], bool(d.get("avisos")))
        if solicitud.accion == "exportar":
            d = self.core.analizador_inteligente_compras.exportar_analisis(p["analisis"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])

__all__ = ["PipelineAnalizadorInteligenteCompras"]
