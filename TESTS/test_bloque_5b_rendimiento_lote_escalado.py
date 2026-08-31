from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from SERVICIOS.calculador_rendimiento_fisico_teorico import CalculadorRendimientoFisicoTeorico
from SERVICIOS.calculador_rentabilidad_escandallos_555b73 import calcular_resumen_economico_555b73
from SERVICIOS.conector_escandallos_real_555 import ConectorEscandallosReal555
from SERVICIOS.escalador_explosion_recetas_556ab import MotorEscaladoExplosion556AB
from SERVICIOS.host_ai_escandallos_read_service import HostAIEscandallosReadService


def _seed(tmp_path: Path) -> None:
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True)
    facturas = tmp_path / "DATOS" / "facturas"
    facturas.mkdir(parents=True)

    (db / "articulos.json").write_text(
        json.dumps(
            [
                {"codigo": "ART-GAMBA", "nombre": "Gamba paella", "precio": 18.0, "unidad": "kg"},
                {"codigo": "ART-PATATA", "nombre": "Patata", "precio": 2.4, "unidad": "kg"},
                {"codigo": "ART-LECHE", "nombre": "Leche", "precio": 1.2, "unidad": "l"},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (db / "proveedores.json").write_text("[]", encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    (facturas / "historico_precios.json").write_text('{"registros":[]}', encoding="utf-8")

    payload = {
        "schema_version": "1.1",
        "escandallos": [
            {
                "receta": {
                    "codigo": "REC-EXCEL-7E82F179E3",
                    "nombre": "Ensaladilla de gamba",
                    "rendimiento": 4,
                    "unidad_rendimiento": "u",
                    "ingredientes": [
                        {"codigo": "ING-GAMBA", "articulo_id": "ART-GAMBA", "nombre": "Gamba paella", "cantidad": 0.19, "unidad": "kg", "coste_unitario": 18.0},
                        {"codigo": "ING-PATATA", "articulo_id": "ART-PATATA", "nombre": "Patata", "cantidad": 0.3, "unidad": "kg", "coste_unitario": 2.4},
                    ],
                },
                "coste_total": 4.14,
            },
            {
                "receta": {
                    "codigo": "REC-EXCEL-F851AC82AC",
                    "nombre": "Crema catalana",
                    "rendimiento": 7,
                    "unidad_rendimiento": "u",
                    "rendimiento_neto": {
                        "cantidad": 1.276,
                        "unidad": "kg",
                        "estado": "CONFIRMADO",
                        "origen": {"tipo": "USUARIO", "referencia": "medicion"},
                    },
                    "ingredientes": [
                        {"codigo": "ING-LECHE", "articulo_id": "ART-LECHE", "nombre": "Leche", "cantidad": 1.4, "unidad": "l", "coste_unitario": 1.2},
                    ],
                },
                "coste_total": 4.085147,
            },
            {
                "receta": {
                    "codigo": "REC-REND-0",
                    "nombre": "Receta rendimiento cero",
                    "rendimiento": 0,
                    "unidad_rendimiento": "u",
                    "ingredientes": [{"nombre": "Base", "cantidad": 1, "unidad": "kg"}],
                },
                "coste_total": 0,
            },
            {
                "receta": {
                    "codigo": "REC-REND-NEG",
                    "nombre": "Receta rendimiento negativo",
                    "rendimiento": -2,
                    "unidad_rendimiento": "u",
                    "ingredientes": [{"nombre": "Base", "cantidad": 1, "unidad": "kg"}],
                },
                "coste_total": 0,
            },
            {
                "receta": {
                    "codigo": "REC-REND-NULL",
                    "nombre": "Receta sin rendimiento",
                    "rendimiento": None,
                    "unidad_rendimiento": "u",
                    "ingredientes": [{"nombre": "Base", "cantidad": 1, "unidad": "kg"}],
                },
                "coste_total": 0,
            },
        ],
    }
    (db / "escandallos_canonicos.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )


def _ingredient_by_name(items: list[dict], name: str) -> dict:
    for item in items:
        item_name = str(item.get("nombre") or item.get("nombre_original") or "")
        if item_name == name:
            return item
    raise AssertionError(f"Ingrediente no encontrado: {name}")


def test_escalado_lote_vs_racion_y_objetivos_arriba_abajo(tmp_path: Path) -> None:
    _seed(tmp_path)
    motor = MotorEscaladoExplosion556AB(tmp_path)

    up = motor.escalar("Ensaladilla de gamba", 10, "u")
    assert up["estado_escalado"] == "CALCULABLE"
    assert up["factor"] == pytest.approx(2.5)
    gamba_up = _ingredient_by_name(up["ingredientes"], "Gamba paella")
    assert gamba_up["cantidad_base"] == pytest.approx(0.19)
    assert gamba_up["cantidad_escalada"] == pytest.approx(0.475)

    down = motor.escalar("Ensaladilla de gamba", 2, "u")
    assert down["estado_escalado"] == "CALCULABLE"
    assert down["factor"] == pytest.approx(0.5)
    gamba_down = _ingredient_by_name(down["ingredientes"], "Gamba paella")
    assert gamba_down["cantidad_escalada"] == pytest.approx(0.095)


def test_rendimiento_y_objetivo_invalidos_no_calculan(tmp_path: Path) -> None:
    _seed(tmp_path)
    motor = MotorEscaladoExplosion556AB(tmp_path)

    cero = motor.escalar("Receta rendimiento cero", 10, "u")
    assert cero["estado_escalado"] == "NO_CALCULABLE"
    assert cero["factor"] is None

    negativo = motor.escalar("Receta rendimiento negativo", 10, "u")
    assert negativo["estado_escalado"] == "NO_CALCULABLE"
    assert negativo["factor"] is None

    nulo = motor.escalar("Receta sin rendimiento", 10, "u")
    assert nulo["estado_escalado"] == "NO_CALCULABLE"
    assert nulo["factor"] is None

    objetivo_nulo = motor.escalar("Ensaladilla de gamba", None, "u")
    assert objetivo_nulo["estado_escalado"] == "NO_CALCULABLE"
    assert objetivo_nulo["factor"] is None


def test_read_dto_mantiene_lote_y_deriva_por_unidad_con_presentacion(tmp_path: Path) -> None:
    _seed(tmp_path)
    dto = HostAIEscandallosReadService(tmp_path).consultar("detalle", escandallo_id="REC-EXCEL-7E82F179E3")["escandallo"]
    gamba = _ingredient_by_name(dto["ingredientes"], "Gamba paella")

    assert gamba["ambito_cantidad"] == "LOTE_COMPLETO"
    assert gamba["cantidad"] == pytest.approx(0.19)
    assert gamba["cantidad_por_unidad_rendimiento"] == pytest.approx(0.0475)
    assert gamba["unidad_cantidad_por_rendimiento"] == "kg/u"
    assert gamba["cantidad_por_unidad_rendimiento_presentacion"]["cantidad"] == pytest.approx(47.5)
    assert gamba["cantidad_por_unidad_rendimiento_presentacion"]["unidad"] == "g/u"


def test_rendimiento_declarado_y_neto_separados_y_coste_racion(tmp_path: Path) -> None:
    _seed(tmp_path)
    dto = HostAIEscandallosReadService(tmp_path).consultar("detalle", escandallo_id="REC-EXCEL-F851AC82AC")["escandallo"]

    assert dto["rendimiento"] == 7
    assert dto["unidad_rendimiento"] == "u"
    assert dto["rendimiento_neto"]["cantidad"] == pytest.approx(1.276)
    assert dto["rendimiento_neto"]["unidad"] == "kg"

    resumen = calcular_resumen_economico_555b73(
        {"coste_total": 4.085147},
        coste_calculado=4.085147,
        rendimiento_calculo=7,
        ingredientes=[{"cantidad": 1.0, "coste_unitario": 1.0}],
    )
    assert resumen["coste_unitario"] == pytest.approx(0.583592)

    resumen_invalido = calcular_resumen_economico_555b73(
        {"coste_total": 4.085147},
        coste_calculado=4.085147,
        rendimiento_calculo=0,
        ingredientes=[{"cantidad": 1.0, "coste_unitario": 1.0}],
    )
    assert resumen_invalido["coste_unitario"] is None
    assert resumen_invalido["estado"] == "RENDIMIENTO_INVALIDO"


def test_rendimiento_teorico_parcial_y_multidimensional(tmp_path: Path) -> None:
    _seed(tmp_path)
    calc = CalculadorRendimientoFisicoTeorico()

    parcial = calc.calcular(
        [
            {"nombre": "Masa", "cantidad": 0.8, "unidad": "kg"},
            {"nombre": "Huevos", "cantidad": 2, "unidad": "u"},
        ],
        rendimiento=4,
        unidad_rendimiento="u",
    )
    assert parcial["estado"] == "PARCIAL"
    assert parcial["por_unidad"]["cantidad"] == pytest.approx(0.2)
    assert parcial["ingredientes_excluidos"][0]["motivo"] == "UNIDAD_DISCRETA_SIN_EQUIVALENCIA_FISICA"

    multi = calc.calcular(
        [
            {"nombre": "Masa", "cantidad": 1, "unidad": "kg"},
            {"nombre": "Liquido", "cantidad": 1, "unidad": "l"},
        ],
        rendimiento=2,
        unidad_rendimiento="u",
    )
    assert multi["estado"] == "COMPLETO"
    assert multi["cantidad"] is None and multi["unidad"] is None
    assert multi["magnitudes"]["masa"]["cantidad"] == pytest.approx(1.0)
    assert multi["magnitudes"]["volumen"]["cantidad"] == pytest.approx(1.0)


def test_conector_read_respeta_escalado_y_no_inventa_con_rendimiento_invalido(tmp_path: Path) -> None:
    _seed(tmp_path)
    conector = ConectorEscandallosReal555(tmp_path)

    ens = conector.consultar("ensaladilla de gamba", personas=10)
    assert ens["encontrado"] is True
    item = ens["coincidencias"][0]
    assert item["estado_escalado"] == "CALCULABLE"
    assert item["factor"] == pytest.approx(2.5)
    gamba = _ingredient_by_name(item["ingredientes"], "Gamba paella")
    assert gamba["cantidad"] == pytest.approx(0.475)

    invalida = conector.consultar("receta sin rendimiento", personas=10)
    assert invalida["coincidencias"][0]["estado_escalado"] == "NO_CALCULABLE"
    assert invalida["coincidencias"][0]["factor"] is None


def test_precision_decimal_en_escalado_019_por_25(tmp_path: Path) -> None:
    _seed(tmp_path)
    motor = MotorEscaladoExplosion556AB(tmp_path)
    out = motor.escalar("Ensaladilla de gamba", Decimal("10"), "u")
    gamba = _ingredient_by_name(out["ingredientes"], "Gamba paella")
    esperado = Decimal("0.19") * Decimal("2.5")
    assert Decimal(str(gamba["cantidad_escalada"])) == esperado
