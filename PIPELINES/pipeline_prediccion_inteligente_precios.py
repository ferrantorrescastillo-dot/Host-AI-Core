from __future__ import annotations

from MODELOS.api_interna import ResultadoPipeline, SolicitudPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelinePrediccionInteligentePrecios(BasePipeline):
    """Pipeline para predicción inteligente de precios.

    Mantiene el patrón oficial de Host AI:
    `SolicitudPipeline -> Pipeline -> Servicio -> ResultadoPipeline`.
    """

    nombre = "prediccion_inteligente_precios"
    descripcion = "Predice precios futuros con histórico, media móvil, tendencia y confianza."
    acciones_soportadas = ["predecir", "predecir_articulo", "exportar"]

    def _resultado_accion_no_implementada(self, accion: str) -> ResultadoPipeline:
        return ResultadoPipeline(
            False,
            self.nombre,
            accion,
            "Acción no implementada.",
            errores=[f"Acción no implementada: {accion}"],
        )

    def _ejecutar(self, solicitud: SolicitudPipeline) -> ResultadoPipeline:
        parametros = solicitud.parametros
        accion = solicitud.accion

        if accion == "predecir":
            datos = self.core.prediccion_inteligente_precios.predecir_precios(parametros.get("ventana", 3))
            return ResultadoPipeline(True, self.nombre, accion, datos["lectura_host_ai"], datos, [], False)

        if accion == "predecir_articulo":
            datos = self.core.prediccion_inteligente_precios.predecir_articulo(
                parametros["articulo_id"],
                parametros.get("ventana", 3),
            )
            return ResultadoPipeline(
                bool(datos.get("encontrado")),
                self.nombre,
                accion,
                datos["lectura_host_ai"],
                datos,
                [],
                False,
            )

        if accion == "exportar":
            datos = self.core.prediccion_inteligente_precios.exportar_prediccion(
                parametros["prediccion"],
                parametros.get("nombre", ""),
            )
            return ResultadoPipeline(True, self.nombre, accion, datos["lectura_host_ai"], datos, [], False)

        return self._resultado_accion_no_implementada(accion)


__all__ = ["PipelinePrediccionInteligentePrecios"]
