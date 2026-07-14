from __future__ import annotations

from MODELOS.api_interna import ResultadoPipeline, SolicitudPipeline
from PIPELINES.base_pipeline import BasePipeline


class PipelineMotorInteligentePedidos(BasePipeline):
    """Pipeline para el motor inteligente de pedidos.

    El pipeline no decide qué comprar: delega la decisión en el servicio
    `motor_inteligente_pedidos` y normaliza la respuesta para el Core.
    """

    nombre = "motor_inteligente_pedidos"
    descripcion = "Genera decisiones inteligentes de compra: comprar, esperar, cambiar proveedor o no comprar."
    acciones_soportadas = ["generar", "generar_articulo", "exportar"]

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

        if accion == "generar":
            datos = self.core.motor_inteligente_pedidos.generar_pedidos_inteligentes(
                parametros.get("horizonte_dias", 14),
                parametros.get("dias_seguridad", 3),
            )
            return ResultadoPipeline(
                True,
                self.nombre,
                accion,
                datos["lectura_host_ai"],
                datos,
                ["Revisar decisiones críticas antes de confirmar pedido."],
                True,
            )

        if accion == "generar_articulo":
            datos = self.core.motor_inteligente_pedidos.generar_pedido_articulo(
                parametros["articulo_id"],
                parametros.get("horizonte_dias", 14),
            )
            return ResultadoPipeline(
                bool(datos.get("encontrado")),
                self.nombre,
                accion,
                datos["lectura_host_ai"],
                datos,
                [],
                True,
            )

        if accion == "exportar":
            datos = self.core.motor_inteligente_pedidos.exportar_pedidos(
                parametros["informe"],
                parametros.get("nombre", ""),
            )
            return ResultadoPipeline(True, self.nombre, accion, datos["lectura_host_ai"], datos, [], False)

        return self._resultado_accion_no_implementada(accion)


__all__ = ["PipelineMotorInteligentePedidos"]
