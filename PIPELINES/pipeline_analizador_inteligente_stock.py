"""Pipeline del analizador inteligente de stock.

RC2.8: documentación interna y contrato público sin cambiar comportamiento."""

from __future__ import annotations
from MODELOS.api_interna import SolicitudPipeline, ResultadoPipeline
from PIPELINES.base_pipeline import BasePipeline

class PipelineAnalizadorInteligenteStock(BasePipeline):
    nombre = "analizador_inteligente_stock"
    descripcion = "Analiza stock actual, mínimos, máximos, críticos, exceso, sin movimiento y valoración económica."
    acciones_soportadas = ["analizar", "exportar"]
    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        p = solicitud.parametros
        if solicitud.accion == "analizar":
            d = self.core.analizador_inteligente_stock.analizar_stock(p.get("dias_sin_movimiento", 30))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        if solicitud.accion == "exportar":
            d = self.core.analizador_inteligente_stock.exportar_analisis(p["analisis"], p.get("nombre", ""))
            return ResultadoPipeline(True, self.nombre, solicitud.accion, d["lectura_host_ai"], d, [], False)
        return ResultadoPipeline(False, self.nombre, solicitud.accion, "Acción no implementada.", errores=[f"Acción no implementada: {solicitud.accion}"])

__all__ = ["PipelineAnalizadorInteligenteStock"]
