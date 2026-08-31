from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any

from CORE.entidades.receta import EstadoRendimiento, Receta
from SERVICIOS.schema_escandallos_555a import normalizar_unidad


class EstadoCompatibilidadRendimiento(str, Enum):
    DIRECTAMENTE_COMPATIBLE = "DIRECTAMENTE_COMPATIBLE"
    COMPATIBLE_CON_CONVERSION = "COMPATIBLE_CON_CONVERSION"
    INCOMPATIBLE = "INCOMPATIBLE"
    INFORMACION_INSUFICIENTE = "INFORMACION_INSUFICIENTE"


@dataclass(frozen=True)
class ResultadoCompatibilidadRendimiento:
    estado: EstadoCompatibilidadRendimiento
    cantidad_en_unidad_rendimiento: float | None = None
    factor_aplicado: float | None = None
    conversion: dict[str, Any] | None = None
    incidencias: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["estado"] = self.estado.value
        return data


class ValidadorCompatibilidadRendimiento:
    """Valida dimensiones del rendimiento sin calcular costes ni modificar estado."""

    _FACTORES = {
        ("kg", "g"): Decimal("1000"),
        ("g", "kg"): Decimal("0.001"),
        ("l", "ml"): Decimal("1000"),
        ("ml", "l"): Decimal("0.001"),
    }

    @classmethod
    def _convertir(cls, cantidad: float, origen: str, destino: str) -> float | None:
        source = normalizar_unidad(origen)
        target = normalizar_unidad(destino)
        if not source or not target:
            return None
        cantidad_dec = Decimal(str(cantidad))
        if source == target:
            return float(cantidad_dec)
        factor = cls._FACTORES.get((source, target))
        return float(cantidad_dec * factor) if factor is not None else None

    def evaluar(
        self,
        cantidad_requerida: float | None,
        unidad_requerida: str,
        receta_hijo: Receta,
    ) -> ResultadoCompatibilidadRendimiento:
        try:
            required = float(cantidad_requerida) if cantidad_requerida is not None else None
            yield_value = float(receta_hijo.rendimiento)
        except (TypeError, ValueError):
            required, yield_value = None, 0.0
        if required is None or required <= 0:
            return ResultadoCompatibilidadRendimiento(
                EstadoCompatibilidadRendimiento.INFORMACION_INSUFICIENTE,
                incidencias=["CANTIDAD_REQUERIDA_INVALIDA"],
            )
        if yield_value <= 0 or not normalizar_unidad(receta_hijo.unidad_rendimiento):
            return ResultadoCompatibilidadRendimiento(
                EstadoCompatibilidadRendimiento.INFORMACION_INSUFICIENTE,
                incidencias=["RENDIMIENTO_INVALIDO"],
            )

        direct = self._convertir(required, unidad_requerida, receta_hijo.unidad_rendimiento)
        if direct is not None:
            direct_dec = Decimal(str(direct))
            yield_dec = Decimal(str(yield_value))
            factor_dec = direct_dec / yield_dec
            return ResultadoCompatibilidadRendimiento(
                EstadoCompatibilidadRendimiento.DIRECTAMENTE_COMPATIBLE,
                cantidad_en_unidad_rendimiento=float(direct_dec),
                factor_aplicado=float(factor_dec),
                conversion={
                    "origen": normalizar_unidad(unidad_requerida),
                    "destino": normalizar_unidad(receta_hijo.unidad_rendimiento),
                    "procedencia": "conversion_metrica_canonica",
                },
            )

        net = receta_hijo.rendimiento_neto
        if net is None:
            return ResultadoCompatibilidadRendimiento(
                EstadoCompatibilidadRendimiento.INFORMACION_INSUFICIENTE,
                incidencias=["RENDIMIENTO_NETO_NO_DISPONIBLE"],
            )
        if net.estado is not EstadoRendimiento.CONFIRMADO:
            return ResultadoCompatibilidadRendimiento(
                EstadoCompatibilidadRendimiento.INFORMACION_INSUFICIENTE,
                incidencias=["RENDIMIENTO_NETO_NO_CONFIRMADO"],
            )
        if net.cantidad <= 0 or not normalizar_unidad(net.unidad):
            return ResultadoCompatibilidadRendimiento(
                EstadoCompatibilidadRendimiento.INFORMACION_INSUFICIENTE,
                incidencias=["RENDIMIENTO_NETO_INVALIDO"],
            )

        required_in_net = self._convertir(required, unidad_requerida, net.unidad)
        if required_in_net is None:
            return ResultadoCompatibilidadRendimiento(
                EstadoCompatibilidadRendimiento.INCOMPATIBLE,
                incidencias=["UNIDAD_NO_COMPATIBLE_CON_RENDIMIENTO_NETO"],
            )
        required_in_net_dec = Decimal(str(required_in_net))
        net_qty_dec = Decimal(str(net.cantidad))
        fraction = required_in_net_dec / net_qty_dec
        yield_dec = Decimal(str(yield_value))
        return ResultadoCompatibilidadRendimiento(
            EstadoCompatibilidadRendimiento.COMPATIBLE_CON_CONVERSION,
            cantidad_en_unidad_rendimiento=float(fraction * yield_dec),
            factor_aplicado=float(fraction),
            conversion={
                "origen": normalizar_unidad(unidad_requerida),
                "destino": normalizar_unidad(receta_hijo.unidad_rendimiento),
                "procedencia": "rendimiento_neto_confirmado",
                "rendimiento_neto": {"cantidad": net.cantidad, "unidad": normalizar_unidad(net.unidad)},
            },
        )


__all__ = [
    "EstadoCompatibilidadRendimiento",
    "ResultadoCompatibilidadRendimiento",
    "ValidadorCompatibilidadRendimiento",
]
