from __future__ import annotations

from decimal import Decimal, InvalidOperation
import json
from typing import Any


UNIT_ALIASES = {
    "u": "u", "ud": "u", "uds": "u", "unidad": "u", "unidades": "u",
    "pieza": "u", "piezas": "u", "pax": "u", "racion": "u", "raciones": "u",
    "kg": "kg", "kilo": "kg", "kilos": "kg", "kilogramo": "kg", "kilogramos": "kg",
    "g": "g", "gr": "g", "gramo": "g", "gramos": "g",
    "l": "l", "lt": "l", "litro": "l", "litros": "l",
    "ml": "ml", "mili": "ml", "mililitro": "ml", "mililitros": "ml",
}

INCIDENT_ALIASES = {
    "PRODUCTO_SIN_PRECIO": "SIN_PRECIO", "SIN_PRECIO": "SIN_PRECIO",
    "CONVERSION_INEXISTENTE": "CONVERSION_NO_DISPONIBLE",
    "UNIDAD_INCOMPATIBLE": "CONVERSION_NO_DISPONIBLE",
    "UNIDADES_INCOMPATIBLES": "CONVERSION_NO_DISPONIBLE",
    "CONVERSION_NO_DISPONIBLE": "CONVERSION_NO_DISPONIBLE",
}


def decimal_value(value: Any) -> Decimal | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    text = str(value).strip().replace("€", "").replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", ".")
    try:
        parsed = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def normalize_unit(value: Any) -> str:
    unit = " ".join(str(value or "").strip().lower().split())
    return UNIT_ALIASES.get(unit, unit)


def normalize_incident_type(value: Any) -> str:
    raw = str(value or "").strip().upper()
    return INCIDENT_ALIASES.get(raw, raw)


def physical_conversion(source: Any, target: Any, factor: Any) -> dict[str, str]:
    source_unit, target_unit = normalize_unit(source), normalize_unit(target)
    parsed = decimal_value(factor)
    if not source_unit or not target_unit or source_unit == target_unit or parsed is None or parsed <= 0:
        raise ValueError("invalid_physical_conversion")
    return {
        "tipo": "CONVERSION_FISICA", "unidad_origen": source_unit,
        "cantidad_origen": "1", "unidad_destino": target_unit,
        "cantidad_destino": format(parsed, "f"),
    }


def parse_conversions(value: Any) -> list[dict[str, str]]:
    raw = value
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            raw = json.loads(text)
        except (ValueError, TypeError):
            return []
    items = raw if isinstance(raw, list) else [raw] if isinstance(raw, dict) else []
    result: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        source = normalize_unit(item.get("unidad_origen"))
        target = normalize_unit(item.get("unidad_destino"))
        source_qty = decimal_value(item.get("cantidad_origen", 1))
        target_qty = decimal_value(item.get("cantidad_destino"))
        if source and target and source != target and source_qty and source_qty > 0 and target_qty and target_qty > 0:
            result.append({
                "tipo": "CONVERSION_FISICA", "unidad_origen": source,
                "cantidad_origen": format(source_qty, "f"), "unidad_destino": target,
                "cantidad_destino": format(target_qty, "f"),
            })
    return result


def merge_physical_conversion(existing: Any, source: Any, target: Any, factor: Any) -> list[dict[str, str]]:
    proposed = physical_conversion(source, target, factor)
    retained = [item for item in parse_conversions(existing) if not (
        item["unidad_origen"] == proposed["unidad_origen"]
        and item["unidad_destino"] == proposed["unidad_destino"]
    )]
    return [*retained, proposed]


def convert_quantity(
    quantity: Any, source: Any, target: Any, article: dict[str, Any] | None = None,
) -> Decimal | None:
    amount = decimal_value(quantity)
    source_unit, target_unit = normalize_unit(source), normalize_unit(target)
    if amount is None or not source_unit or not target_unit:
        return None
    if source_unit == target_unit:
        return amount
    metric = {"g": ("mass", Decimal("1")), "kg": ("mass", Decimal("1000")),
              "ml": ("volume", Decimal("1")), "l": ("volume", Decimal("1000"))}
    if source_unit in metric and target_unit in metric and metric[source_unit][0] == metric[target_unit][0]:
        return amount * metric[source_unit][1] / metric[target_unit][1]
    for conversion in parse_conversions((article or {}).get("conversion_unidades")):
        origin_qty = Decimal(conversion["cantidad_origen"])
        destination_qty = Decimal(conversion["cantidad_destino"])
        if source_unit == conversion["unidad_origen"] and target_unit == conversion["unidad_destino"]:
            return amount * destination_qty / origin_qty
        if source_unit == conversion["unidad_destino"] and target_unit == conversion["unidad_origen"]:
            return amount * origin_qty / destination_qty
    return None


__all__ = [
    "convert_quantity", "decimal_value", "merge_physical_conversion",
    "normalize_incident_type", "normalize_unit", "parse_conversions", "physical_conversion",
]
