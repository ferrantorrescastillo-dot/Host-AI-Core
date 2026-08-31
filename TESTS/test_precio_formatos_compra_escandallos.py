from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path

from SERVICIOS.articulos_catalog_read_service import ArticulosCatalogReadService
from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService
from SERVICIOS.motor_calculo_escandallos_601 import (
    INC_UNIDAD_INCOMPATIBLE,
    MotorCalculoEscandallos601,
)
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


def _repo(tmp_path: Path, articles: list[dict]) -> RepositorioProductosMaestro601:
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True)
    (db / "articulos.json").write_text(
        json.dumps(articles, ensure_ascii=False), encoding="utf-8"
    )
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    invoices = tmp_path / "DATOS" / "facturas"
    invoices.mkdir(parents=True)
    (invoices / "historico_precios.json").write_text(
        '{"registros":[]}', encoding="utf-8"
    )
    return RepositorioProductosMaestro601(tmp_path)


def _calculate(motor: MotorCalculoEscandallos601, code: str, quantity: float, unit: str) -> dict:
    return motor.calcular(
        nombre_escandallo="Fixture aislado",
        numero_raciones=1,
        lineas_entrada=[{
            "producto_codigo": code,
            "nombre_mostrado": code,
            "cantidad_neta": quantity,
            "unidad_receta": unit,
        }],
    )["lineas"][0]


def test_paquete_seis_unidades_preserva_precio_comercial_y_normaliza_sin_redondeo_precoz(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path, [{
        "codigo": "ART-HUEVO",
        "nombre": "Huevo L",
        "precio": 1.60,
        # La base kg es solo una sugerencia: unidad_formato es la evidencia canónica.
        "catalogo_maestro": {
            "unidad_compra": "paquete",
            "cantidad_formato": "6",
            "unidad_formato": "u",
            "unidad_base": "kg",
            "unidad_base_sugerida": True,
        },
    }])
    product = repo.obtener_producto("ART-HUEVO")
    assert product is not None
    assert product["precio"] == 1.60
    assert product["unidad_compra"] == "paquete"
    assert product["cantidad_formato"] == "6"
    assert product["unidad_formato"] == "u"

    motor = MotorCalculoEscandallos601(repo)
    normalized, unit, issues = motor.precio_catalogo_normalizado(product)
    assert normalized is not None
    assert abs(Decimal(str(normalized)) - (Decimal("1.60") / Decimal("6"))) < Decimal("1e-15")
    assert unit == "u"
    assert issues == []

    line = _calculate(motor, "ART-HUEVO", 7, "u")
    assert line["unidad_precio"] == "u"
    assert line["precio_compra_utilizado"] == 0.266667
    assert line["coste_linea"] == 1.866667
    assert f'{line["coste_linea"]:.2f}' == "1.87"
    assert line["coste_linea"] != 1.82
    assert not any(
        issue["tipo"] == INC_UNIDAD_INCOMPATIBLE for issue in line["incidencias"]
    )


def test_formato_sin_cantidad_no_se_reinterpreta_como_precio_unitario(tmp_path: Path) -> None:
    repo = _repo(tmp_path, [{
        "codigo": "ART-CAJA",
        "nombre": "Caja incompleta",
        "precio": 12,
        "unidad": "u",
        "catalogo_maestro": {
            "unidad_compra": "caja",
            "unidad_formato": "u",
            "unidad_base": "u",
        },
    }])
    motor = MotorCalculoEscandallos601(repo)
    product = repo.obtener_producto("ART-CAJA")
    normalized, unit, issues = motor.precio_catalogo_normalizado(product or {})
    assert normalized is None
    assert unit == ""
    assert [issue["tipo"] for issue in issues] == [INC_UNIDAD_INCOMPATIBLE]
    line = _calculate(motor, "ART-CAJA", 1, "u")
    assert line["precio_compra_utilizado"] is None
    assert line["coste_linea"] is None
    assert any(issue["tipo"] == INC_UNIDAD_INCOMPATIBLE for issue in line["incidencias"])


def test_formato_sin_unidad_con_base_sugerida_no_inventa_kg(tmp_path: Path) -> None:
    repo = _repo(tmp_path, [{
        "codigo": "ART-PACK",
        "nombre": "Paquete sin unidad de contenido",
        "precio": 8,
        "catalogo_maestro": {
            "unidad_compra": "paquete",
            "cantidad_formato": "4",
        },
    }])
    product = repo.obtener_producto("ART-PACK") or {}
    normalized, unit, issues = MotorCalculoEscandallos601(repo).precio_catalogo_normalizado(product)
    assert product["unidad_base"] == "kg"
    assert product["unidad_base_sugerida"] is True
    assert normalized is None
    assert unit == ""
    assert issues[0]["tipo"] == INC_UNIDAD_INCOMPATIBLE


def test_producto_metrico_normal_conserva_precio_por_kg(tmp_path: Path) -> None:
    repo = _repo(tmp_path, [{
        "codigo": "ART-HARINA",
        "nombre": "Harina",
        "precio": 2.40,
        "unidad": "kg",
        "catalogo_maestro": {"unidad_base": "kg"},
    }])
    line = _calculate(MotorCalculoEscandallos601(repo), "ART-HARINA", 0.5, "kg")
    assert line["precio_compra_utilizado"] == 2.4
    assert line["coste_linea"] == 1.2
    assert not any(
        issue["tipo"] == INC_UNIDAD_INCOMPATIBLE for issue in line["incidencias"]
    )


def test_regresion_metrica_kg_g_y_l_ml(tmp_path: Path) -> None:
    repo = _repo(tmp_path, [
        {
            "codigo": "ART-AZUCAR", "nombre": "Azúcar", "precio": 4,
            "unidad": "kg", "catalogo_maestro": {"unidad_base": "kg"},
        },
        {
            "codigo": "ART-LECHE", "nombre": "Leche", "precio": 2,
            "unidad": "l", "catalogo_maestro": {"unidad_base": "l"},
        },
    ])
    motor = MotorCalculoEscandallos601(repo)
    sugar = _calculate(motor, "ART-AZUCAR", 250, "g")
    milk = _calculate(motor, "ART-LECHE", 500, "ml")
    assert sugar["factor_conversion"] == 0.001
    assert sugar["coste_linea"] == 1
    assert milk["factor_conversion"] == 0.001
    assert milk["coste_linea"] == 1


def test_catalogo_read_expone_unidad_de_contenido_sin_escribir_datos(tmp_path: Path) -> None:
    repo = _repo(tmp_path, [{
        "codigo": "ART-BOTELLAS",
        "nombre": "Caja de botellas",
        "precio": 24,
        "unidad": "u",
        "catalogo_maestro": {
            "unidad_compra": "caja",
            "cantidad_formato": "12",
            "unidad_formato": "u",
            "unidad_base": "u",
        },
    }])
    before = (tmp_path / "DATOS" / "db" / "articulos.json").read_bytes()
    article = ArticulosCatalogReadService(tmp_path).obtener("ART-BOTELLAS")["articulo"]
    after = (tmp_path / "DATOS" / "db" / "articulos.json").read_bytes()
    assert article["precio"] == 24
    assert article["unidad_compra"] == "caja"
    assert article["cantidad_formato"] == 12
    assert article["unidad_formato"] == "u"
    assert before == after


def test_crema_catalana_fixture_read_calcula_siete_unidades_del_pack(tmp_path: Path) -> None:
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True)
    (db / "escandallos_canonicos.json").write_text(json.dumps({
        "schema_version": "1.0",
        "escandallos": [{
            "receta": {
                "codigo": "REC-CREMA-FIXTURE",
                "nombre": "Crema catalana fixture",
                "rendimiento": 1,
                "unidad_rendimiento": "u",
                "ingredientes": [{
                    "articulo_id": "ART-HUEVO-FIXTURE",
                    "nombre": "Huevo fixture",
                    "cantidad": 7,
                    "unidad": "u",
                }],
            },
        }],
    }, ensure_ascii=False), encoding="utf-8")
    (db / "articulos.json").write_text(json.dumps([{
        "codigo": "ART-HUEVO-FIXTURE",
        "nombre": "Huevo fixture",
        "precio": 1.60,
        "proveedor": "Proveedor fixture",
        "catalogo_maestro": {
            "unidad_compra": "paquete",
            "cantidad_formato": "6",
            "unidad_formato": "u",
            "unidad_base": "kg",
            "unidad_base_sugerida": True,
            "proveedor_preferente": "Proveedor fixture",
            "fecha_precio": "2026-08-14",
        },
    }], ensure_ascii=False), encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    invoices = tmp_path / "DATOS" / "facturas"
    invoices.mkdir(parents=True)
    (invoices / "historico_precios.json").write_text(
        '{"registros":[]}', encoding="utf-8"
    )

    result = BibliotecaCulinariaReadService(tmp_path).detalle("REC-CREMA-FIXTURE")
    costing = result["elaboracion"]["escandallo"]
    line = costing["lineas"][0]
    assert line["cantidad"] == 7
    assert line["unidad"] == "u"
    assert line["precio_original"] == 1.6
    assert line["unidad_precio_original"] == "paquete"
    assert line["precio_aplicado"] == 0.266667
    assert line["unidad_precio_aplicado"] == "u"
    assert line["coste_linea"] == 1.866667
    assert f'{line["coste_linea"]:.2f}' == "1.87"
    assert line["proveedor_precio"] == "Proveedor fixture"
    assert line["estado_coste"] == "DISPONIBLE"
    assert line["motivo_sin_coste"] is None
    assert costing["estado_coste"] == "DISPONIBLE"
    assert costing["coste_total"] == 1.866667
