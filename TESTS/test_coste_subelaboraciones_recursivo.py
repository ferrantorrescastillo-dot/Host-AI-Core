from __future__ import annotations

import json
from pathlib import Path

import pytest

from CORE.entidades.receta import EstadoRendimiento, OrigenRendimiento, Receta, RendimientoNeto
from SERVICIOS.calculador_coste_subelaboraciones import CalculadorCosteSubelaboraciones
from SERVICIOS.host_ai_escandallos_read_service import HostAIEscandallosReadService


def _recipe(amount: float, unit: str, net: RendimientoNeto | None = None) -> Receta:
    return Receta("HIJO", "Hijo", amount, unit, rendimiento_neto=net)


def _calculate(recipe: Receta, quantity: float, unit: str, total: float = 10) -> dict:
    return CalculadorCosteSubelaboraciones().calcular(
        parent_id="PADRE", line_id="L1", child_id="HIJO",
        required_quantity=quantity, required_unit=unit, child_recipe=recipe,
        child_costing={"estado_coste": "DISPONIBLE", "coste_total": total}, depth=1,
    )


@pytest.mark.parametrize(("recipe", "quantity", "unit", "total", "expected"), [
    (_recipe(1, "kg"), 0.02, "kg", 10, 0.2),
    (_recipe(1000, "g"), 0.02, "kg", 10, 0.2),
    (_recipe(7, "u", RendimientoNeto(1.26, "kg", EstadoRendimiento.CONFIRMADO,
                                     OrigenRendimiento("USUARIO"))), 0.18, "kg", 14, 2.0),
])
def test_coste_proporcional_directo_metrico_y_neto_confirmado(
    recipe: Receta, quantity: float, unit: str, total: float, expected: float,
) -> None:
    result = _calculate(recipe, quantity, unit, total)
    assert result["coste_linea"] == expected
    assert result["estado_coste"] == "COSTE_SUBELABORACION_RESUELTO"
    assert result["trazabilidad_coste"]["escandallo_padre_id"] == "PADRE"
    assert result["trazabilidad_coste"]["escandallo_hijo_id"] == "HIJO"


@pytest.mark.parametrize("net", [
    None,
    RendimientoNeto(1.26, "kg", EstadoRendimiento.SUGERIDO, OrigenRendimiento("SISTEMA")),
    RendimientoNeto(1.26, "kg", EstadoRendimiento.IMPORTADO, OrigenRendimiento("EXCEL")),
])
def test_no_calcula_sin_rendimiento_neto_confirmado(net: RendimientoNeto | None) -> None:
    result = _calculate(_recipe(7, "u", net), 0.18, "kg", 14)
    assert result["coste_linea"] is None
    assert result["estado_coste"] == "RENDIMIENTO_INSUFICIENTE"


def test_no_calcula_coste_hijo_incompleto_ni_unidades_incompatibles() -> None:
    calculator = CalculadorCosteSubelaboraciones()
    incomplete = calculator.calcular(
        parent_id="P", line_id="L", child_id="H", required_quantity=1,
        required_unit="kg", child_recipe=_recipe(1, "kg"),
        child_costing={"estado_coste": "PARCIAL", "coste_total": None}, depth=1,
    )
    incompatible = _calculate(_recipe(1, "kg"), 1, "l")
    units_without_net = _calculate(_recipe(7, "u"), 1, "kg")
    assert incomplete["estado_coste"] == "COSTE_HIJO_INCOMPLETO"
    assert incompatible["estado_coste"] == "RENDIMIENTO_INSUFICIENTE"
    assert units_without_net["estado_coste"] == "RENDIMIENTO_INSUFICIENTE"
    assert all(item["coste_linea"] is None for item in (incomplete, incompatible, units_without_net))


def _write_fixture(base: Path, recipes: list[dict], articles: list[dict]) -> None:
    db = base / "DATOS" / "db"
    db.mkdir(parents=True)
    (db / "escandallos_canonicos.json").write_text(json.dumps({
        "schema_version": "1.1", "escandallos": [{"receta": item} for item in recipes],
    }), encoding="utf-8")
    (db / "articulos.json").write_text(json.dumps(articles), encoding="utf-8")
    (db / "proveedores.json").write_text("[]", encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    invoices = base / "DATOS" / "facturas"
    invoices.mkdir(parents=True)
    (invoices / "historico_precios.json").write_text('{"registros":[]}', encoding="utf-8")


def _ingredient(name: str, quantity: float, unit: str, *, child: str | None = None,
                article: str | None = None) -> dict:
    item = {"nombre": name, "cantidad": quantity, "unidad": unit}
    if child:
        item["metadata"] = {"tipo": "ELABORACION", "referencia_elaboracion": child}
    if article:
        item["articulo_id"] = article
    return item


def test_fixture_rec_crema_resuelve_dos_niveles_repetidos_y_preserva_read(tmp_path: Path) -> None:
    recipes = [{
        "codigo": "REC-CREMA", "nombre": "Crema fixture", "rendimiento": 7,
        "unidad_rendimiento": "u", "rendimiento_neto": {
            "cantidad": 1.26, "unidad": "kg", "estado": "CONFIRMADO",
            "origen": {"tipo": "USUARIO"},
        },
        "ingredientes": [_ingredient("Base", 1, "kg", article="ART-BASE")],
    }, {
        "codigo": "REC-PADRE-CREMA", "nombre": "Padre crema fixture", "rendimiento": 1,
        "unidad_rendimiento": "u", "ingredientes": [
            _ingredient("Crema fixture", 0.18, "kg", child="Crema fixture"),
            _ingredient("Crema fixture", 0.18, "kg", child="Crema fixture"),
        ],
    }]
    _write_fixture(tmp_path, recipes, [{
        "codigo": "ART-BASE", "nombre": "Base", "precio": 14, "unidad": "kg",
    }])
    before = (tmp_path / "DATOS/db/escandallos_canonicos.json").read_bytes()

    detail = HostAIEscandallosReadService(tmp_path).consultar(
        "detalle", escandallo_id="REC-PADRE-CREMA",
    )["escandallo"]

    assert [line["coste_linea"] for line in detail["ingredientes"]] == [2.0, 2.0]
    assert detail["costes"]["coste_total"] == 4.0
    assert detail["costes"]["estado_coste"] == "DISPONIBLE"
    assert (tmp_path / "DATOS/db/escandallos_canonicos.json").read_bytes() == before


def test_tres_niveles_resuelven_y_ciclo_hijo_inexistente_quedan_null(tmp_path: Path) -> None:
    recipes = [
        {"codigo": "C", "nombre": "C", "rendimiento": 1, "unidad_rendimiento": "kg",
         "ingredientes": [_ingredient("Base", 1, "kg", article="ART-BASE")]},
        {"codigo": "B", "nombre": "B", "rendimiento": 1, "unidad_rendimiento": "kg",
         "ingredientes": [_ingredient("C", 0.5, "kg", child="C")]},
        {"codigo": "A", "nombre": "A", "rendimiento": 1, "unidad_rendimiento": "kg",
         "ingredientes": [_ingredient("B", 0.5, "kg", child="B")]},
        {"codigo": "X", "nombre": "X", "rendimiento": 1, "unidad_rendimiento": "kg",
         "ingredientes": [_ingredient("Y", 1, "kg", child="Y")]},
        {"codigo": "Y", "nombre": "Y", "rendimiento": 1, "unidad_rendimiento": "kg",
         "ingredientes": [_ingredient("X", 1, "kg", child="X")]},
        {"codigo": "MISSING-PARENT", "nombre": "Missing parent", "rendimiento": 1,
         "unidad_rendimiento": "kg", "ingredientes": [
             _ingredient("No existe", 1, "kg", child="No existe")
         ]},
    ]
    _write_fixture(tmp_path, recipes, [{
        "codigo": "ART-BASE", "nombre": "Base", "precio": 8, "unidad": "kg",
    }])
    service = HostAIEscandallosReadService(tmp_path)
    three = service.consultar("detalle", escandallo_id="A")["escandallo"]
    cycle = service.consultar("detalle", escandallo_id="X")["escandallo"]
    missing = service.consultar("detalle", escandallo_id="MISSING-PARENT")["escandallo"]
    assert three["costes"]["coste_total"] == 2.0
    assert cycle["ingredientes"][0]["coste_linea"] is None
    assert cycle["ingredientes"][0]["estado_coste"] == "CICLO_DETECTADO"
    assert any(i["tipo"] == "CICLO_DETECTADO" for i in cycle["costes"]["incidencias"])
    assert missing["ingredientes"][0]["estado_coste"] == "SUBELABORACION_NO_ENCONTRADA"


def test_profundidad_excedida_no_presenta_coste_total(tmp_path: Path) -> None:
    recipes = []
    for index in range(15):
        child = f"N{index + 1}" if index < 14 else None
        ingredients = (
            [_ingredient(child, 1, "kg", child=child)] if child
            else [_ingredient("Base", 1, "kg", article="ART-BASE")]
        )
        recipes.append({"codigo": f"N{index}", "nombre": f"N{index}", "rendimiento": 1,
                        "unidad_rendimiento": "kg", "ingredientes": ingredients})
    _write_fixture(tmp_path, recipes, [{
        "codigo": "ART-BASE", "nombre": "Base", "precio": 1, "unidad": "kg",
    }])
    detail = HostAIEscandallosReadService(tmp_path).consultar(
        "detalle", escandallo_id="N0",
    )["escandallo"]
    assert detail["costes"]["coste_total"] is None
    assert detail["costes"]["estado_coste"] in {"SIN_COSTE", "PARCIAL"}
    assert any(
        item["tipo"] == "PROFUNDIDAD_EXCEDIDA"
        for item in detail["costes"]["incidencias"]
    )
