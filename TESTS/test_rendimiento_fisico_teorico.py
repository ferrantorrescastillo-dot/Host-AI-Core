from __future__ import annotations

import json
from pathlib import Path

from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService
from SERVICIOS.calculador_rendimiento_fisico_teorico import CalculadorRendimientoFisicoTeorico


def _calculate(lines: list[dict], rendimiento: object = 1, unit: str = "u") -> dict:
    return CalculadorRendimientoFisicoTeorico().calcular(
        lines, rendimiento=rendimiento, unidad_rendimiento=unit,
    )


def test_suma_kg_g_completa_y_deriva_por_unidad() -> None:
    result = _calculate([
        {"nombre": "A", "cantidad": 0.8, "unidad": "kg"},
        {"nombre": "B", "cantidad": 200, "unidad": "g"},
    ], rendimiento=5)
    assert result["estado"] == "COMPLETO"
    assert result["cantidad"] == 1
    assert result["unidad"] == "kg"
    assert result["por_unidad"] == {
        "cantidad": 0.2, "unidad": "kg/u", "estado_confirmacion": "SUGERIDO",
        "calculo_parcial": False,
    }
    assert result["estado_confirmacion"] == "SUGERIDO"


def test_masa_mas_unidades_sin_peso_es_parcial_y_no_inventa_gramos() -> None:
    result = _calculate([
        {"nombre": "Base", "cantidad": 0.8, "unidad": "kg"},
        {"nombre": "Huevos", "cantidad": 2, "unidad": "u"},
    ], rendimiento=4)
    assert result["estado"] == "PARCIAL"
    assert result["cantidad"] == 0.8
    assert result["por_unidad"]["cantidad"] == 0.2
    assert result["por_unidad"]["calculo_parcial"] is True
    assert result["ingredientes_excluidos"] == [{
        "articulo_id": None, "nombre": "Huevos", "cantidad": 2,
        "unidad": "u", "motivo": "UNIDAD_DISCRETA_SIN_EQUIVALENCIA_FISICA",
    }]


def test_conversion_fisica_explicita_unidad_a_kg_completa_la_masa() -> None:
    result = _calculate([
        {"nombre": "Base", "cantidad": 0.8, "unidad": "kg"},
        {
            "articulo_id": "ART-PAN", "nombre": "Pan", "cantidad": 2, "unidad": "u",
            "conversion_unidades": [{
                "tipo": "CONVERSION_FISICA", "unidad_origen": "u",
                "cantidad_origen": "1", "unidad_destino": "kg",
                "cantidad_destino": "0.050",
            }],
        },
    ], rendimiento=2)
    assert result["estado"] == "COMPLETO"
    assert result["cantidad"] == 0.9
    assert result["ingredientes_excluidos"] == []
    assert result["ingredientes_incluidos"][1]["cantidad_normalizada"] == 0.1


def test_formato_comercial_no_se_infiere_como_conversion_fisica() -> None:
    result = _calculate([
        {"nombre": "Base", "cantidad": 1, "unidad": "kg"},
        {
            "nombre": "Caja de piezas", "cantidad": 2, "unidad": "u",
            "unidad_compra": "caja", "cantidad_formato": 64,
            "unidad_formato": "u", "unidad_base": "u",
        },
    ])
    assert result["estado"] == "PARCIAL"
    assert result["ingredientes_excluidos"][0]["motivo"] == "UNIDAD_DISCRETA_SIN_EQUIVALENCIA_FISICA"


def test_suma_l_ml_sin_convertir_a_masa() -> None:
    result = _calculate([
        {"nombre": "A", "cantidad": 0.5, "unidad": "l"},
        {"nombre": "B", "cantidad": 250, "unidad": "ml"},
    ])
    assert result["estado"] == "COMPLETO"
    assert result["cantidad"] == 0.75
    assert result["unidad"] == "l"
    assert "masa" not in result["magnitudes"]


def test_masa_y_volumen_se_mantienen_separados() -> None:
    result = _calculate([
        {"nombre": "Masa", "cantidad": 1, "unidad": "kg"},
        {"nombre": "Líquido", "cantidad": 1, "unidad": "l"},
    ], rendimiento=2)
    assert result["estado"] == "COMPLETO"
    assert result["cantidad"] is None and result["unidad"] is None
    assert result["magnitudes"] == {
        "masa": {"cantidad": 1.0, "unidad": "kg"},
        "volumen": {"cantidad": 1.0, "unidad": "l"},
    }
    assert result["por_unidad"] is None
    assert result["incidencias"][-1]["codigo"] == "RESULTADO_MULTIDIMENSIONAL"


def test_rendimiento_cero_null_y_solo_unidades_no_se_convierten_en_cero() -> None:
    zero_yield = _calculate([{"nombre": "A", "cantidad": 1.4, "unidad": "kg"}], rendimiento=0)
    assert zero_yield["cantidad"] == 1.4
    assert zero_yield["por_unidad"] is None
    null_quantity = _calculate([{"nombre": "A", "cantidad": None, "unidad": "kg"}])
    assert null_quantity["estado"] == "NO_CALCULABLE"
    assert null_quantity["cantidad"] is None
    units = _calculate([{"nombre": "Huevos", "cantidad": 7, "unidad": "u"}], rendimiento=7)
    assert units["estado"] == "NO_CALCULABLE"
    assert units["por_unidad"] is None


def test_biblioteca_proyecta_sugerencia_read_sin_persistir(tmp_path: Path) -> None:
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True)
    path = db / "escandallos_canonicos.json"
    path.write_text(json.dumps({
        "schema_version": "1.0", "escandallos": [{"receta": {
            "codigo": "REC-TEORICA", "nombre": "Elaboración teórica",
            "rendimiento": 7, "unidad_rendimiento": "u",
            "rendimiento_neto": None,
            "ingredientes": [
                {"nombre": "Base", "cantidad": 1.4, "unidad": "kg"},
                {"nombre": "Huevos", "cantidad": 7, "unidad": "u"},
            ],
        }}],
    }, ensure_ascii=False), encoding="utf-8")
    (db / "articulos.json").write_text("[]", encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    invoices = tmp_path / "DATOS" / "facturas"
    invoices.mkdir(parents=True)
    (invoices / "historico_precios.json").write_text('{"registros":[]}', encoding="utf-8")
    before = path.read_bytes()
    detail = BibliotecaCulinariaReadService(tmp_path).detalle("REC-TEORICA")["elaboracion"]
    theoretical = detail["receta"]["rendimiento_fisico_teorico"]
    assert theoretical["estado"] == "PARCIAL"
    assert theoretical["cantidad"] == 1.4
    assert theoretical["por_unidad"]["cantidad"] == 0.2
    assert detail["receta"]["rendimiento"] == 7
    assert detail["receta"]["rendimiento_neto"] is None
    assert theoretical["datos_reales_modificados"] is False
    assert path.read_bytes() == before
