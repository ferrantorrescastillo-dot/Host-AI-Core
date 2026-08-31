from __future__ import annotations

import json
from pathlib import Path

import pytest

from CORE.entidades.receta import EstadoRendimiento, OrigenRendimiento, Receta, RendimientoNeto
from SERVICIOS.calculador_coste_subelaboraciones import CalculadorCosteSubelaboraciones
from SERVICIOS.host_ai_escandallos_read_service import HostAIEscandallosReadService


def _receta_hijo(rendimiento: float, unidad: str, net: RendimientoNeto | None = None) -> Receta:
    return Receta(
        codigo="HIJO",
        nombre="Hijo",
        rendimiento=rendimiento,
        unidad_rendimiento=unidad,
        rendimiento_neto=net,
    )


def _calc_simple(
    *,
    required_quantity: float | None,
    required_unit: str,
    child_rendimiento: float,
    child_unidad: str,
    child_total: float,
    child_estado: str = "DISPONIBLE",
    child_net: RendimientoNeto | None = None,
):
    return CalculadorCosteSubelaboraciones().calcular(
        parent_id="PADRE",
        line_id="L1",
        child_id="HIJO",
        required_quantity=required_quantity,
        required_unit=required_unit,
        child_recipe=_receta_hijo(child_rendimiento, child_unidad, child_net),
        child_costing={"estado_coste": child_estado, "coste_total": child_total},
        depth=1,
    )


def _seed(base: Path, recipes: list[dict], articles: list[dict]) -> None:
    db = base / "DATOS" / "db"
    db.mkdir(parents=True)
    (db / "escandallos_canonicos.json").write_text(
        json.dumps({"schema_version": "1.1", "escandallos": [{"receta": r} for r in recipes]}, ensure_ascii=False),
        encoding="utf-8",
    )
    (db / "articulos.json").write_text(json.dumps(articles, ensure_ascii=False), encoding="utf-8")
    (db / "proveedores.json").write_text("[]", encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    inv = base / "DATOS" / "facturas"
    inv.mkdir(parents=True)
    (inv / "historico_precios.json").write_text('{"registros":[]}', encoding="utf-8")


def _ing(nombre: str, cantidad: float | None, unidad: str, *, receta_id: str | None = None, art: str | None = None) -> dict:
    row = {"nombre": nombre, "cantidad": cantidad, "unidad": unidad}
    if receta_id:
        row["receta_id"] = receta_id
        row["metadata"] = {"tipo": "ELABORACION", "referencia_elaboracion": nombre}
    if art:
        row["articulo_id"] = art
    return row


def _line_by_name(lines: list[dict], name: str) -> dict:
    for line in lines:
        if str(line.get("nombre_original") or line.get("nombre") or "") == name:
            return line
    raise AssertionError(name)


def test_hijo_simple_fraccion_y_conversiones_metricas():
    # 12€ / 2kg = 6€/kg; padre usa 0.150kg -> 0.9€
    out = _calc_simple(
        required_quantity=0.150,
        required_unit="kg",
        child_rendimiento=2,
        child_unidad="kg",
        child_total=12,
    )
    assert out["estado_coste"] == "COSTE_SUBELABORACION_RESUELTO"
    assert out["coste_linea"] == pytest.approx(0.9)

    # kg <- g
    kg_g = _calc_simple(
        required_quantity=150,
        required_unit="g",
        child_rendimiento=2,
        child_unidad="kg",
        child_total=12,
    )
    assert kg_g["coste_linea"] == pytest.approx(0.9)

    # l <- ml
    l_ml = _calc_simple(
        required_quantity=250,
        required_unit="ml",
        child_rendimiento=2,
        child_unidad="l",
        child_total=10,
    )
    assert l_ml["coste_linea"] == pytest.approx(1.25)


def test_rechazo_unidad_incompatible_y_hijo_sin_rendimiento():
    incompatible = _calc_simple(
        required_quantity=0.5,
        required_unit="kg",
        child_rendimiento=10,
        child_unidad="u",
        child_total=20,
    )
    assert incompatible["coste_linea"] is None
    assert incompatible["estado_coste"] == "RENDIMIENTO_INSUFICIENTE"

    null_yield = _calc_simple(
        required_quantity=0.5,
        required_unit="kg",
        child_rendimiento=0,
        child_unidad="kg",
        child_total=20,
    )
    assert null_yield["coste_linea"] is None
    assert null_yield["estado_coste"] == "RENDIMIENTO_INSUFICIENTE"

    neg_yield = _calc_simple(
        required_quantity=0.5,
        required_unit="kg",
        child_rendimiento=-3,
        child_unidad="kg",
        child_total=20,
    )
    assert neg_yield["coste_linea"] is None
    assert neg_yield["estado_coste"] == "RENDIMIENTO_INSUFICIENTE"


def test_hijo_coste_parcial_se_propaga_y_nulls_no_son_cero():
    child_partial = _calc_simple(
        required_quantity=0.2,
        required_unit="kg",
        child_rendimiento=1,
        child_unidad="kg",
        child_total=10,
        child_estado="PARCIAL",
    )
    assert child_partial["coste_linea"] is None
    assert child_partial["estado_coste"] == "COSTE_HIJO_INCOMPLETO"

    qty_null = _calc_simple(
        required_quantity=None,
        required_unit="kg",
        child_rendimiento=1,
        child_unidad="kg",
        child_total=10,
    )
    assert qty_null["coste_linea"] is None
    assert qty_null["estado_coste"] == "RENDIMIENTO_INSUFICIENTE"


def test_decimal_sin_redondeo_prematuro_en_cadena_simple():
    # 1/3 -> coste unitario periódico; *3 debe cerrar exactamente en el total por fracción 1
    out = _calc_simple(
        required_quantity=3,
        required_unit="u",
        child_rendimiento=3,
        child_unidad="u",
        child_total=1,
    )
    assert out["coste_linea"] == pytest.approx(1.0)


def test_read_multinivel_a_b_c_y_coste_proporcional(tmp_path: Path):
    recipes = [
        {
            "codigo": "C",
            "nombre": "Comp C",
            "rendimiento": 1,
            "unidad_rendimiento": "kg",
            "ingredientes": [_ing("Base C", 1, "kg", art="ART-C")],
        },
        {
            "codigo": "B",
            "nombre": "Comp B",
            "rendimiento": 1,
            "unidad_rendimiento": "kg",
            "ingredientes": [_ing("Comp C", 0.5, "kg", receta_id="C")],
        },
        {
            "codigo": "A",
            "nombre": "Comp A",
            "rendimiento": 1,
            "unidad_rendimiento": "kg",
            "ingredientes": [_ing("Comp B", 0.5, "kg", receta_id="B")],
        },
    ]
    _seed(tmp_path, recipes, [{"codigo": "ART-C", "nombre": "Base C", "precio": 8, "unidad": "kg"}])

    dto_b = HostAIEscandallosReadService(tmp_path).consultar("detalle", escandallo_id="B")["escandallo"]
    dto_a = HostAIEscandallosReadService(tmp_path).consultar("detalle", escandallo_id="A")["escandallo"]

    line_b = _line_by_name(dto_b["ingredientes"], "Comp C")
    line_a = _line_by_name(dto_a["ingredientes"], "Comp B")

    assert line_b["coste_linea"] == pytest.approx(4.0)
    assert dto_b["costes"]["coste_total"] == pytest.approx(4.0)
    assert line_a["coste_linea"] == pytest.approx(2.0)
    assert dto_a["costes"]["coste_total"] == pytest.approx(2.0)


def test_read_ciclos_autorreferencia_y_referencia_rota_con_traza(tmp_path: Path):
    recipes = [
        {"codigo": "A", "nombre": "A", "rendimiento": 1, "unidad_rendimiento": "kg", "ingredientes": [_ing("B", 1, "kg", receta_id="B")]},
        {"codigo": "B", "nombre": "B", "rendimiento": 1, "unidad_rendimiento": "kg", "ingredientes": [_ing("A", 1, "kg", receta_id="A")]},
        {"codigo": "SELF", "nombre": "SELF", "rendimiento": 1, "unidad_rendimiento": "kg", "ingredientes": [_ing("SELF", 1, "kg", receta_id="SELF")]},
        {"codigo": "BROKEN", "nombre": "BROKEN", "rendimiento": 1, "unidad_rendimiento": "kg", "ingredientes": [_ing("No existe", 1, "kg", receta_id="NO-ID")]},
        # ID correcto con nombre cambiado: debe resolver por ID
        {"codigo": "HIJO-ID", "nombre": "Nombre nuevo hijo", "rendimiento": 1, "unidad_rendimiento": "kg", "ingredientes": [_ing("Base", 1, "kg", art="ART-X")]},
        {"codigo": "PADRE-ID", "nombre": "Padre con nombre antiguo", "rendimiento": 1, "unidad_rendimiento": "kg", "ingredientes": [
            {"nombre": "Nombre antiguo", "cantidad": 0.5, "unidad": "kg", "receta_id": "HIJO-ID", "metadata": {"tipo": "ELABORACION", "referencia_elaboracion": "Nombre antiguo"}}
        ]},
        # ID roto con nombre que coincide con existente: no debe resolver por nombre
        {"codigo": "PADRE-ID-ROTO", "nombre": "Padre id roto", "rendimiento": 1, "unidad_rendimiento": "kg", "ingredientes": [
            {"nombre": "Nombre nuevo hijo", "cantidad": 0.5, "unidad": "kg", "receta_id": "ID-ROTO", "metadata": {"tipo": "ELABORACION", "referencia_elaboracion": "Nombre nuevo hijo"}}
        ]},
    ]
    _seed(tmp_path, recipes, [{"codigo": "ART-X", "nombre": "Base", "precio": 6, "unidad": "kg"}])
    read = HostAIEscandallosReadService(tmp_path)

    ciclo = read.consultar("detalle", escandallo_id="A")["escandallo"]
    self_cycle = read.consultar("detalle", escandallo_id="SELF")["escandallo"]
    broken = read.consultar("detalle", escandallo_id="BROKEN")["escandallo"]
    id_ok = read.consultar("detalle", escandallo_id="PADRE-ID")["escandallo"]
    id_broken = read.consultar("detalle", escandallo_id="PADRE-ID-ROTO")["escandallo"]

    line_ciclo = _line_by_name(ciclo["ingredientes"], "B")
    assert line_ciclo["estado_coste"] == "CICLO_DETECTADO"
    assert line_ciclo["coste_linea"] is None
    assert any(i["tipo"] == "CICLO_DETECTADO" for i in ciclo["costes"]["incidencias"])
    assert line_ciclo["trazabilidad_coste"]["ruta"]

    line_self = _line_by_name(self_cycle["ingredientes"], "SELF")
    assert line_self["estado_coste"] == "CICLO_DETECTADO"
    assert line_self["coste_linea"] is None

    line_broken = _line_by_name(broken["ingredientes"], "No existe")
    assert line_broken["estado_coste"] == "SUBELABORACION_NO_ENCONTRADA"
    assert line_broken["coste_linea"] is None
    assert broken["costes"]["coste_total"] is None

    # ID gana sobre nombre
    line_id_ok = _line_by_name(id_ok["ingredientes"], "Nombre antiguo")
    assert line_id_ok["escandallo_hijo_id"] == "HIJO-ID"
    assert line_id_ok["estado_coste"] == "COSTE_SUBELABORACION_RESUELTO"
    assert line_id_ok["coste_linea"] == pytest.approx(3.0)

    # ID roto no usa fallback por nombre
    line_id_roto = _line_by_name(id_broken["ingredientes"], "Nombre nuevo hijo")
    assert line_id_roto["escandallo_hijo_id"] == "ID-ROTO"
    assert line_id_roto["estado_relacion"] == "elaboracion_id_roto"
    assert line_id_roto["estado_coste"] == "SUBELABORACION_NO_ENCONTRADA"
    assert line_id_roto["coste_linea"] is None


def test_read_propagacion_parcial_al_padre_y_escalado_no_muta_coste_unitario_hijo(tmp_path: Path):
    recipes = [
        {"codigo": "HIJO-PARCIAL", "nombre": "Hijo parcial", "rendimiento": 1, "unidad_rendimiento": "kg", "ingredientes": [
            _ing("Base", 1, "kg", art="ART-COSTE"),
            _ing("Sin coste", 1, "kg"),
        ]},
        {"codigo": "PADRE", "nombre": "Padre", "rendimiento": 4, "unidad_rendimiento": "u", "ingredientes": [
            _ing("Hijo parcial", 0.5, "kg", receta_id="HIJO-PARCIAL"),
            _ing("Base padre", 0.2, "kg", art="ART-PADRE"),
        ]},
    ]
    _seed(
        tmp_path,
        recipes,
        [
            {"codigo": "ART-COSTE", "nombre": "Base", "precio": 8, "unidad": "kg"},
            {"codigo": "ART-PADRE", "nombre": "Base padre", "precio": 10, "unidad": "kg"},
        ],
    )
    dto = HostAIEscandallosReadService(tmp_path).consultar("detalle", escandallo_id="PADRE")["escandallo"]
    line_hijo = _line_by_name(dto["ingredientes"], "Hijo parcial")

    assert line_hijo["estado_coste"] == "COSTE_HIJO_INCOMPLETO"
    assert line_hijo["coste_linea"] is None
    assert dto["costes"]["estado_coste"] in {"PARCIAL", "SIN_COSTE"}
    assert dto["costes"]["coste_total"] is None
    assert dto["costes"]["coste_total_parcial"] == pytest.approx(2.0)

    # Cantidad padre se mantiene por lote y el derivado por ración queda en capa 5B
    assert line_hijo["cantidad"] == pytest.approx(0.5)
    assert line_hijo["ambito_cantidad"] == "LOTE_COMPLETO"
