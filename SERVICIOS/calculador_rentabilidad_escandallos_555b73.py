from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _first_number(sources: Iterable[Dict[str, Any]], keys: Iterable[str]) -> float | None:
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key in keys:
            if key not in source:
                continue
            value = _float(source.get(key), default=-1.0)
            if value >= 0:
                return value
    return None


@dataclass(slots=True)
class ResumenEconomicoEscandallo555B73:
    coste_total: float
    rendimiento: float
    coste_unitario: float
    precio_venta_unitario: float | None
    iva_pct: float | None
    beneficio_bruto_unitario: float | None
    beneficio_sobre_coste_pct: float | None
    margen_bruto_pct: float | None
    food_cost_pct: float | None
    ingredientes_sin_precio: int
    estado: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def calcular_resumen_economico_555b73(
    escandallo: Dict[str, Any],
    *,
    coste_calculado: float,
    rendimiento_calculo: float,
    ingredientes: list[Dict[str, Any]],
) -> Dict[str, Any]:
    """Calcula la lectura económica de un escandallo sin inventar datos.

    El precio de venta y el IVA son opcionales. Si no están presentes en el
    modelo canónico, los porcentajes dependientes del PVP quedan a ``None``.
    """
    raw = escandallo.get("raw") if isinstance(escandallo.get("raw"), dict) else {}
    receta_raw = raw.get("receta") if isinstance(raw.get("receta"), dict) else {}
    sources = (escandallo, raw, receta_raw)

    coste_base_raw = _first_number(sources, ("coste_total", "coste_receta", "coste"))
    coste_total = round(coste_calculado if coste_calculado > 0 else (coste_base_raw or 0.0), 6)
    rendimiento = max(_float(rendimiento_calculo, 1.0), 1e-9)
    coste_unitario = round(coste_total / rendimiento, 6)

    precio_venta = _first_number(
        sources,
        (
            "precio_venta_unitario",
            "precio_venta",
            "pvp_unitario",
            "pvp",
            "precio_venta_racion",
        ),
    )
    if precio_venta is not None and precio_venta <= 0:
        precio_venta = None

    iva_pct = _first_number(sources, ("iva_pct", "iva", "porcentaje_iva"))
    if iva_pct is not None and iva_pct < 0:
        iva_pct = None

    sin_precio = 0
    for ing in ingredientes:
        cantidad = _float(ing.get("cantidad"), 0.0)
        precio = _float(ing.get("coste_unitario") or ing.get("precio"), 0.0)
        if cantidad > 0 and precio <= 0:
            sin_precio += 1

    beneficio = margen = rentabilidad_coste = food_cost = None
    if precio_venta is not None:
        beneficio = round(precio_venta - coste_unitario, 6)
        margen = round((beneficio / precio_venta) * 100, 4) if precio_venta else None
        rentabilidad_coste = round((beneficio / coste_unitario) * 100, 4) if coste_unitario > 0 else None
        food_cost = round((coste_unitario / precio_venta) * 100, 4) if precio_venta else None

    if coste_total <= 0:
        estado = "COSTE_INCOMPLETO"
    elif sin_precio:
        estado = "COSTE_PARCIAL"
    elif precio_venta is None:
        estado = "PENDIENTE_PRECIO_VENTA"
    elif beneficio is not None and beneficio < 0:
        estado = "VENTA_A_PERDIDA"
    else:
        estado = "RENTABILIDAD_CALCULADA"

    return ResumenEconomicoEscandallo555B73(
        coste_total=coste_total,
        rendimiento=round(rendimiento, 6),
        coste_unitario=coste_unitario,
        precio_venta_unitario=round(precio_venta, 6) if precio_venta is not None else None,
        iva_pct=round(iva_pct, 4) if iva_pct is not None else None,
        beneficio_bruto_unitario=beneficio,
        beneficio_sobre_coste_pct=rentabilidad_coste,
        margen_bruto_pct=margen,
        food_cost_pct=food_cost,
        ingredientes_sin_precio=sin_precio,
        estado=estado,
    ).to_dict()
