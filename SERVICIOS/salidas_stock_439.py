from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from SERVICIOS.motor_movimientos_stock_437 import MotorMovimientosStock437, ResultadoMovimientoStock


@dataclass
class ResultadoSalidaStock:
    ok: bool
    codigo: str
    articulo: str
    cantidad: float
    stock_antes: float
    stock_despues: float
    motivo: str
    tipo_salida: str
    mensaje: str
    id_movimiento: Optional[str] = None


class SalidasStock439:
    """
    Registra salidas manuales de stock usando el motor 4.3.7.

    Tipos de salida:
    - produccion
    - merma
    - rotura
    - consumo_interno
    - ajuste_operativo
    """

    TIPOS_SALIDA = {
        "produccion",
        "merma",
        "rotura",
        "consumo_interno",
        "ajuste_operativo",
    }

    def __init__(
        self,
        ruta_stock: str = "DATOS/db/stock_inicial.json",
        ruta_movimientos: str = "DATOS/db/stock_movimientos.json",
    ) -> None:
        self.motor = MotorMovimientosStock437(ruta_stock, ruta_movimientos)

    def registrar_salida(
        self,
        codigo: str,
        cantidad: Any,
        tipo_salida: str,
        motivo: str,
        usuario: str = "usuario_local",
        documento_relacionado: Optional[str] = None,
    ) -> ResultadoSalidaStock:
        tipo = str(tipo_salida or "").strip().lower()

        if tipo not in self.TIPOS_SALIDA:
            raise ValueError(
                f"Tipo de salida no válido: {tipo_salida}. "
                f"Usa uno de: {', '.join(sorted(self.TIPOS_SALIDA))}"
            )

        motivo_completo = f"{tipo}: {motivo}"

        resultado: ResultadoMovimientoStock = self.motor.registrar_movimiento(
            codigo=codigo,
            cantidad=cantidad,
            tipo="salida",
            motivo=motivo_completo,
            usuario=usuario,
            documento_relacionado=documento_relacionado,
        )

        return ResultadoSalidaStock(
            ok=resultado.ok,
            codigo=resultado.codigo,
            articulo=resultado.articulo,
            cantidad=resultado.cantidad,
            stock_antes=resultado.stock_antes,
            stock_despues=resultado.stock_despues,
            motivo=motivo,
            tipo_salida=tipo,
            mensaje=resultado.mensaje,
            id_movimiento=resultado.id_movimiento,
        )


__all__ = ["SalidasStock439", "ResultadoSalidaStock"]
