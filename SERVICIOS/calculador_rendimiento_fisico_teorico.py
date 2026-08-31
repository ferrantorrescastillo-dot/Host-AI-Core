from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from SERVICIOS.articulo_economico_canonico import convert_quantity, normalize_unit


class CalculadorRendimientoFisicoTeorico:
    """Proyección READ: suma magnitudes compatibles sin inferir densidades."""

    _UNITS = {
        "kg": ("masa", "kg", Decimal("1")),
        "g": ("masa", "kg", Decimal("0.001")),
        "l": ("volumen", "l", Decimal("1")),
        "ml": ("volumen", "l", Decimal("0.001")),
    }

    def calcular(
        self, ingredientes: list[dict[str, Any]], *, rendimiento: Any,
        unidad_rendimiento: str,
    ) -> dict[str, Any]:
        totals = {"masa": Decimal("0"), "volumen": Decimal("0")}
        included: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []

        for index, ingredient in enumerate(ingredientes):
            name = str(
                ingredient.get("nombre_original")
                or ingredient.get("nombre_articulo")
                or ingredient.get("nombre")
                or f"Ingrediente {index + 1}"
            )
            quantity = self._decimal(
                ingredient.get("cantidad_neta")
                if ingredient.get("cantidad_neta") is not None
                else ingredient.get("cantidad")
            )
            base = normalize_unit(ingredient.get("unidad") or ingredient.get("unidad_receta"))
            if quantity is None:
                excluded.append(self._excluded(name, ingredient, "CANTIDAD_DESCONOCIDA"))
                continue
            if quantity < 0:
                excluded.append(self._excluded(name, ingredient, "CANTIDAD_INVALIDA"))
                continue
            conversion = self._UNITS.get(base)
            if conversion is not None:
                dimension, target_unit, factor = conversion
                conversion = (dimension, target_unit, quantity * factor)
            if conversion is None:
                conversion = self._physical_conversion(quantity, base, ingredient)
            if conversion is None:
                reason = (
                    "UNIDAD_DISCRETA_SIN_EQUIVALENCIA_FISICA"
                    if base == "u" else "UNIDAD_NO_CONVERTIBLE"
                )
                excluded.append(self._excluded(name, ingredient, reason))
                continue
            dimension, target_unit, normalized = conversion
            totals[dimension] += normalized
            included.append({
                "articulo_id": ingredient.get("articulo_id"),
                "nombre": name,
                "cantidad_original": float(quantity),
                "unidad_original": base,
                "dimension": dimension,
                "cantidad_normalizada": float(normalized),
                "unidad_normalizada": target_unit,
            })

        magnitudes = {}
        if any(row["dimension"] == "masa" for row in included):
            magnitudes["masa"] = {"cantidad": float(totals["masa"]), "unidad": "kg"}
        if any(row["dimension"] == "volumen" for row in included):
            magnitudes["volumen"] = {"cantidad": float(totals["volumen"]), "unidad": "l"}

        issues: list[dict[str, str]] = []
        if excluded:
            issues.append({
                "codigo": "CALCULO_PARCIAL",
                "detalle": "Existen ingredientes sin magnitud física convertible.",
            })
        if len(magnitudes) > 1:
            issues.append({
                "codigo": "RESULTADO_MULTIDIMENSIONAL",
                "detalle": "Masa y volumen se presentan por separado; no se combinan.",
            })

        if not magnitudes:
            state = "NO_CALCULABLE"
        elif excluded:
            state = "PARCIAL"
        else:
            state = "COMPLETO"

        single = next(iter(magnitudes.values())) if len(magnitudes) == 1 else None
        per_unit = self._per_unit(single, rendimiento, unidad_rendimiento, state)
        return {
            "estado": state,
            "cantidad": single["cantidad"] if single else None,
            "unidad": single["unidad"] if single else None,
            "estado_confirmacion": "SUGERIDO",
            "magnitudes": magnitudes,
            "ingredientes_incluidos": included,
            "ingredientes_excluidos": excluded,
            "por_unidad": per_unit,
            "incidencias": issues,
            "datos_reales_modificados": False,
        }

    @staticmethod
    def _physical_conversion(
        quantity: Decimal, source_unit: str, ingredient: dict[str, Any],
    ) -> tuple[str, str, Decimal] | None:
        """Usa solo relaciones físicas explícitas; nunca deriva formato comercial."""
        for dimension, target in (("masa", "kg"), ("volumen", "l")):
            converted = convert_quantity(quantity, source_unit, target, ingredient)
            if converted is not None:
                return dimension, target, converted
        return None

    @classmethod
    def _per_unit(
        cls, single: dict[str, Any] | None, rendimiento: Any,
        unidad_rendimiento: str, state: str,
    ) -> dict[str, Any] | None:
        declared = cls._decimal(rendimiento)
        unit = str(unidad_rendimiento or "").strip().lower()
        if single is None or declared is None or declared <= 0 or unit not in {"u", "unidad", "unidades"}:
            return None
        quantity = Decimal(str(single["cantidad"])) / declared
        return {
            "cantidad": float(quantity),
            "unidad": f'{single["unidad"]}/u',
            "estado_confirmacion": "SUGERIDO",
            "calculo_parcial": state == "PARCIAL",
        }

    @staticmethod
    def _decimal(value: Any) -> Decimal | None:
        if value in (None, ""):
            return None
        try:
            parsed = Decimal(str(value).replace(",", "."))
        except (InvalidOperation, ValueError):
            return None
        return parsed if parsed.is_finite() else None

    @staticmethod
    def _excluded(name: str, ingredient: dict[str, Any], reason: str) -> dict[str, Any]:
        return {
            "articulo_id": ingredient.get("articulo_id"),
            "nombre": name,
            "cantidad": ingredient.get("cantidad_neta") if ingredient.get("cantidad_neta") is not None else ingredient.get("cantidad"),
            "unidad": ingredient.get("unidad") or ingredient.get("unidad_receta") or None,
            "motivo": reason,
        }


__all__ = ["CalculadorRendimientoFisicoTeorico"]
