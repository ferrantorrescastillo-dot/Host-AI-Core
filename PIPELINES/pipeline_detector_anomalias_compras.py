from __future__ import annotations

from MODELOS.api_interna import ResultadoPipeline, SolicitudPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineDetectorAnomaliasCompras(BasePipeline):
    """Pipeline de entrada para el detector inteligente de anomalías de compras.

    Responsabilidad del pipeline:
    - validar la acción solicitada de forma mínima,
    - delegar la lógica real en el servicio `detector_anomalias_compras`,
    - devolver siempre un `ResultadoPipeline` homogéneo.

    La lógica de negocio permanece en el servicio. Este archivo solo orquesta.
    """

    nombre = "detector_anomalias_compras"
    descripcion = "Detecta anomalías inteligentes en compras, facturas, precios, stock y proveedores."
    acciones_soportadas = ["detectar", "exportar"]

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

        if accion == "detectar":
            datos = self.core.detector_anomalias_compras.detectar_anomalias()
            return ResultadoPipeline(
                True,
                self.nombre,
                accion,
                datos["lectura_host_ai"],
                datos,
                [],
                bool(datos.get("criticas")),
            )

        if accion == "exportar":
            datos = self.core.detector_anomalias_compras.exportar_informe(
                parametros["informe"],
                parametros.get("nombre", ""),
            )
            return ResultadoPipeline(True, self.nombre, accion, datos["lectura_host_ai"], datos, [], False)

        return self._resultado_accion_no_implementada(accion)


__all__ = ["PipelineDetectorAnomaliasCompras"]
