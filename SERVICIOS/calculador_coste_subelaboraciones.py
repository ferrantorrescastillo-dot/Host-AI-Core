from __future__ import annotations

from decimal import Decimal
from typing import Any

from CORE.entidades.receta import Receta
from SERVICIOS.validador_compatibilidad_rendimiento import (
    EstadoCompatibilidadRendimiento,
    ValidadorCompatibilidadRendimiento,
)


class CalculadorCosteSubelaboraciones:
    """Calcula una linea padre-hijo sin resolver identidades ni persistir resultados."""

    def __init__(self, validator: ValidadorCompatibilidadRendimiento | None = None) -> None:
        self.validator = validator or ValidadorCompatibilidadRendimiento()

    def calcular(
        self,
        *,
        parent_id: str,
        line_id: str,
        child_id: str,
        required_quantity: float | None,
        required_unit: str,
        child_recipe: Receta,
        child_costing: dict[str, Any],
        depth: int,
    ) -> dict[str, Any]:
        child_total = child_costing.get("coste_total")
        if child_costing.get("estado_coste") != "DISPONIBLE" or child_total is None:
            return self.unresolved(
                "COSTE_HIJO_INCOMPLETO",
                "El coste completo de la subelaboracion no esta disponible.",
            )
        compatibility = self.validator.evaluar(
            required_quantity, required_unit, child_recipe,
        )
        if compatibility.estado not in {
            EstadoCompatibilidadRendimiento.DIRECTAMENTE_COMPATIBLE,
            EstadoCompatibilidadRendimiento.COMPATIBLE_CON_CONVERSION,
        } or compatibility.factor_aplicado is None:
            issue = (compatibility.incidencias or ["RENDIMIENTO_INSUFICIENTE"])[0]
            state = (
                "UNIDADES_INCOMPATIBLES"
                if compatibility.estado is EstadoCompatibilidadRendimiento.INCOMPATIBLE
                else "RENDIMIENTO_INSUFICIENTE"
            )
            return self.unresolved(state, issue)

        fraction = Decimal(str(compatibility.factor_aplicado))
        cost = fraction * Decimal(str(child_total))
        return {
            "estado_coste": "COSTE_SUBELABORACION_RESUELTO",
            "coste_linea": float(cost),
            "motivo_sin_coste": None,
            "trazabilidad_coste": {
                "escandallo_padre_id": parent_id,
                "linea_padre_id": line_id,
                "escandallo_hijo_id": child_id,
                "coste_total_hijo": float(child_total),
                "rendimiento_declarado": {
                    "cantidad": child_recipe.rendimiento,
                    "unidad": child_recipe.unidad_rendimiento,
                },
                "rendimiento_neto": (
                    {
                        "cantidad": child_recipe.rendimiento_neto.cantidad,
                        "unidad": child_recipe.rendimiento_neto.unidad,
                        "estado": child_recipe.rendimiento_neto.estado.value,
                    }
                    if child_recipe.rendimiento_neto else None
                ),
                "conversion": compatibility.conversion,
                "fraccion_lote": float(fraction),
                "coste_resultante": float(cost),
                "profundidad": depth,
                "estado": "COSTE_SUBELABORACION_RESUELTO",
            },
        }

    @staticmethod
    def unresolved(state: str, reason: str, trace: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "estado_coste": state,
            "coste_linea": None,
            "motivo_sin_coste": reason,
            "trazabilidad_coste": dict(trace) if trace else None,
        }


__all__ = ["CalculadorCosteSubelaboraciones"]
