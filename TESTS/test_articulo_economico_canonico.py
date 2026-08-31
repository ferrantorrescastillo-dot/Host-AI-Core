from __future__ import annotations

from decimal import Decimal

import pytest

from SERVICIOS.articulo_economico_canonico import (
    convert_quantity,
    merge_physical_conversion,
    normalize_incident_type,
    normalize_unit,
)


@pytest.mark.parametrize(("alias", "canonical"), (
    ("unidad", "u"), ("uds", "u"), ("gramos", "g"),
    ("kilogramos", "kg"), ("litros", "l"), ("mililitros", "ml"),
))
def test_unidad_canonica_unica(alias: str, canonical: str) -> None:
    assert normalize_unit(alias) == canonical


@pytest.mark.parametrize(("quantity", "source", "target", "expected"), (
    (250, "g", "kg", Decimal("0.25")),
    (1, "kg", "g", Decimal("1000")),
    (100, "ml", "l", Decimal("0.1")),
    (1, "l", "ml", Decimal("1000")),
))
def test_conversion_metrica_canonica(quantity, source: str, target: str, expected: Decimal) -> None:
    assert convert_quantity(quantity, source, target) == expected


@pytest.mark.parametrize(("factor", "target", "expected"), (
    ("0.325", "kg", Decimal("0.325")),
    ("0,75", "l", Decimal("0.75")),
))
def test_conversion_fisica_explicita_es_bidireccional(factor: str, target: str, expected: Decimal) -> None:
    article = {"conversion_unidades": merge_physical_conversion([], "u", target, factor)}
    assert convert_quantity(1, "u", target, article) == expected
    assert convert_quantity(expected, target, "u", article) == Decimal("1")


@pytest.mark.parametrize("historical", (
    "CONVERSION_INEXISTENTE", "UNIDAD_INCOMPATIBLE", "UNIDADES_INCOMPATIBLES",
))
def test_taxonomia_historica_converge_en_incidencia_estable(historical: str) -> None:
    assert normalize_incident_type(historical) == "CONVERSION_NO_DISPONIBLE"
