from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from SERVICIOS.articulos_catalog_read_service import ArticulosCatalogReadService
from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService


class _AggregateBiblioteca(BibliotecaCulinariaReadService):
    def __init__(self, summaries): self.summaries = list(summaries)
    def _all_recipes(self, incluir_archivadas=False): return list(self.summaries)
    def _cost_context(self, recipes): return {}
    def _summary(self, recipe, cost_context=None): return dict(recipe)


def test_busqueda_canonica_incluye_alias_recipe_id_y_pendientes() -> None:
    base = {
        "codigo": "TABLA-QUESOS", "categoria": "Aperitivos", "estado": "PENDIENTE_DE_COMPLETAR",
        "actualizado_en": None, "coste_por_racion": None, "tiene_receta": True,
        "tiene_escandallo": True, "tiene_ficha_tecnica": False, "tiene_documentos": False,
    }
    service = _AggregateBiblioteca([
        {**base, "id": "REC601-000042", "nombre": "Tabla de quesos", "aliases": ["Selección de quesos"]},
        {**base, "id": "REC601-000043", "nombre": "Tabla de quesos", "aliases": ["Quesos Boronat"]},
    ])
    assert [item["id"] for item in service.listar({"q": "tabla de quesos", "page_size": 100})["elaboraciones"]["items"]] == ["REC601-000042", "REC601-000043"]
    assert service.listar({"q": "seleccion de quesos"})["elaboraciones"]["items"][0]["id"] == "REC601-000042"
    assert service.listar({"q": "REC601-000043"})["elaboraciones"]["items"][0]["id"] == "REC601-000043"


def _economic(receta_id, cost, *, state="DISPONIBLE", complete=True, yield_value=10, total=None):
    return {
        "id": receta_id, "nombre": f"Receta {receta_id}", "estado_coste": state,
        "coste_completo": complete, "coste_por_racion": cost,
        "coste_total": cost if total is None else total, "rendimiento": yield_value, "raciones": yield_value,
    }


def test_agregacion_economica_vacia_una_y_todas_invalidas():
    empty = _AggregateBiblioteca([]).agregar_costes("MAX_COSTE_POR_RACION")
    assert empty["estado"] == "SIN_RESULTADOS" and empty["total_evaluadas"] == 0
    one = _AggregateBiblioteca([_economic("REC-1", "1.25")]).agregar_costes("MAX_COSTE_POR_RACION")
    assert one["resultado"] == [{"receta_id": "REC-1", "nombre": "Receta REC-1", "coste_por_racion": 1.25}]
    invalid = _AggregateBiblioteca([
        _economic("PARCIAL", 99, state="PARCIAL", complete=False),
        _economic("SIN-PRECIO", None, state="SIN_PRECIO", complete=False),
        _economic("SIN-CONVERSION", 80, state="SIN_CONVERSION", complete=False),
        _economic("NULL", None), _economic("YIELD-0", 70, yield_value=0),
        _economic("NAN", float("nan")),
    ]).agregar_costes("MAX_COSTE_POR_RACION")
    assert invalid["estado"] == "SIN_RESULTADOS" and invalid["total_validas"] == 0


def test_agregacion_max_min_empate_y_cero_real_disponible():
    service = _AggregateBiblioteca([
        _economic("REC-ZERO", 0), _economic("REC-MID", "1.10"),
        _economic("REC-MAX-B", "2.50"), _economic("REC-MAX-A", Decimal("2.500")),
        _economic("REC-PARCIAL", 100, state="PARCIAL", complete=False),
    ])
    maximum = service.agregar_costes("MAX_COSTE_POR_RACION")
    minimum = service.agregar_costes("MIN_COSTE_POR_RACION")
    assert [item["receta_id"] for item in maximum["resultado"]] == ["REC-MAX-A", "REC-MAX-B"]
    assert maximum["total_evaluadas"] == 5 and maximum["total_validas"] == 4 and maximum["total_excluidas"] == 1
    assert minimum["resultado"][0]["receta_id"] == "REC-ZERO" and minimum["resultado"][0]["coste_por_racion"] == 0
    assert maximum["datos_reales_modificados"] is False


def test_agregacion_coste_total_y_23_registros_no_depende_del_limite_visual():
    rows = [_economic(f"REC-{index:02d}", index / 10, total=index + 1) for index in range(23)]
    service = _AggregateBiblioteca(rows)
    maximum = service.agregar_costes("MAX_COSTE_TOTAL")
    minimum = service.agregar_costes("MIN_COSTE_TOTAL")
    assert maximum["total_evaluadas"] == maximum["total_validas"] == 23
    assert maximum["resultado"][0] == {"receta_id": "REC-22", "nombre": "Receta REC-22", "coste_total": 23.0}
    assert minimum["resultado"][0]["receta_id"] == "REC-00"


def test_conteos_economicos_reutilizan_coste_completo_y_desglosan_estados():
    rows = [
        _economic("OK", "1.00"),
        _economic("PARCIAL", None, state="PARCIAL", complete=False),
        _economic("PRECIO", None, state="SIN_PRECIO", complete=False),
        _economic("CONVERSION", None, state="SIN_CONVERSION", complete=False),
        _economic("NO-CALC", None, state="NO_CALCULABLE", complete=False),
        # El rendimiento invalido excluye del ranking por racion, pero el coste sigue completo.
        _economic("YIELD", "9.00", yield_value=0),
    ]
    service = _AggregateBiblioteca(rows)
    incomplete = service.agregar_costes("COUNT_COSTE_INCOMPLETO")
    available = service.agregar_costes("COUNT_COSTE_DISPONIBLE")
    assert incomplete == {
        "ok": True, "agregacion": "COUNT_COSTE_INCOMPLETO", "estado": "OK",
        "total_evaluadas": 6, "total_disponibles": 2, "total_incompletas": 4,
        "conteo": 4,
        "desglose": {"NO_CALCULABLE": 1, "PARCIAL": 1, "SIN_CONVERSION": 1, "SIN_PRECIO": 1},
        "candidatos_economicos": [
            {"receta_id": "PARCIAL", "nombre": "Receta PARCIAL", "estado_coste": "PARCIAL"},
            {"receta_id": "PRECIO", "nombre": "Receta PRECIO", "estado_coste": "SIN_PRECIO"},
            {"receta_id": "CONVERSION", "nombre": "Receta CONVERSION", "estado_coste": "SIN_CONVERSION"},
            {"receta_id": "NO-CALC", "nombre": "Receta NO-CALC", "estado_coste": "NO_CALCULABLE"},
        ],
        "datos_reales_modificados": False,
    }
    assert available["conteo"] == 2 and available["desglose"] == {"DISPONIBLE": 2}


def test_conteos_vacio_todas_disponibles_todas_incompletas_y_27_registros():
    assert _AggregateBiblioteca([]).agregar_costes("COUNT_COSTE_INCOMPLETO")["conteo"] == 0
    all_available = _AggregateBiblioteca([_economic(f"OK-{i}", i) for i in range(27)])
    assert all_available.agregar_costes("COUNT_COSTE_DISPONIBLE")["conteo"] == 27
    all_incomplete = _AggregateBiblioteca([
        _economic(f"BAD-{i}", None, state="SIN_COSTE", complete=False) for i in range(27)
    ])
    counted = all_incomplete.agregar_costes("COUNT_COSTE_INCOMPLETO")
    assert counted["total_evaluadas"] == counted["conteo"] == 27
    assert counted["datos_reales_modificados"] is False


def test_ranking_denso_decimal_empates_asc_desc_y_posicion_inexistente():
    service = _AggregateBiblioteca([
        _economic("MAX-B", Decimal("10.00")), _economic("MAX-A", Decimal("10.0")),
        _economic("SECOND", Decimal("8.000")),
        _economic("THIRD-A", Decimal("2.50")), _economic("THIRD-B", Decimal("2.500")),
        _economic("ZERO", Decimal("0")),
        _economic("PARTIAL", 999, state="PARCIAL", complete=False),
    ])
    desc1 = service.agregar_costes("RANK_COSTE_POR_RACION", orden="DESC", posicion=1)
    desc2 = service.agregar_costes("RANK_COSTE_POR_RACION", orden="DESC", posicion=2)
    asc1 = service.agregar_costes("RANK_COSTE_POR_RACION", orden="ASC", posicion=1)
    asc2 = service.agregar_costes("RANK_COSTE_POR_RACION", orden="ASC", posicion=2)
    missing = service.agregar_costes("RANK_COSTE_POR_RACION", orden="DESC", posicion=10)
    assert [x["receta_id"] for x in desc1["resultado"]] == ["MAX-A", "MAX-B"]
    assert desc1["resultado"] == service.agregar_costes("MAX_COSTE_POR_RACION")["resultado"]
    assert desc2["resultado"][0]["receta_id"] == "SECOND" and desc2["posicion"] == 2
    assert asc1["resultado"] == service.agregar_costes("MIN_COSTE_POR_RACION")["resultado"]
    assert asc2["numero_empates"] == 2
    assert [x["receta_id"] for x in asc2["resultado"]] == ["THIRD-A", "THIRD-B"]
    assert missing["estado"] == "POSICION_NO_DISPONIBLE" and missing["resultado"] == []


def test_listado_global_incompletas_filtra_estado_y_no_confunde_rendimiento():
    rows = [
        _economic("OK", 1), _economic("YIELD", 2, yield_value=0),
        _economic("PARTIAL", None, state="PARCIAL", complete=False),
        _economic("NO-ESC", None, state="SIN_ESCANDALLO", complete=False),
        _economic("PRICE", None, state="SIN_PRECIO", complete=False),
        _economic("CONV", None, state="SIN_CONVERSION", complete=False),
    ]
    service = _AggregateBiblioteca(rows)
    all_items = service.listar_costes_incompletos()
    partial = service.listar_costes_incompletos(estado_coste="PARCIAL")
    assert all_items["total_evaluadas"] == 6 and all_items["total_coincidencias"] == 4
    assert all_items["items_devueltos"] == 4 and all_items["truncado"] is False
    assert {item["receta_id"] for item in all_items["resultado"]} == {"PARTIAL", "NO-ESC", "PRICE", "CONV"}
    assert partial["total_coincidencias"] == 1
    assert partial["resultado"][0]["estado_coste"] == "PARCIAL"
    assert all(item["coste_completo"] is False for item in all_items["resultado"])
    assert all_items["datos_reales_modificados"] is False


def test_listado_incompletas_vacio_o_ninguna_y_paginacion_global_mayor_de_diez():
    assert _AggregateBiblioteca([]).listar_costes_incompletos()["total_coincidencias"] == 0
    assert _AggregateBiblioteca([_economic("OK", 1)]).listar_costes_incompletos()["resultado"] == []
    rows = [_economic(f"BAD-{index:02d}", None, state="PARCIAL", complete=False) for index in range(27)]
    service = _AggregateBiblioteca(rows)
    first = service.listar_costes_incompletos(limite=10, pagina=1)
    third = service.listar_costes_incompletos(limite=10, pagina=3)
    assert first["total_coincidencias"] == 27 and first["items_devueltos"] == 10 and first["truncado"] is True
    assert third["items_devueltos"] == 7 and third["truncado"] is False


def test_detalle_causal_parcial_sin_escandallo_disponible_y_sin_causa_inventada():
    class Details(_AggregateBiblioteca):
        def __init__(self, detail): self.detail_value = detail
        def detalle(self, _identity): return {"ok": True, "elaboracion": dict(self.detail_value)}

    partial = Details({
        "id": "PARTIAL", "nombre": "Parcial", "estado_coste": "PARCIAL", "coste_completo": False,
        "escandallo": {"lineas": [
            {"articulo_id": "ART-1", "nombre_articulo": "Patata", "coste_linea": None,
             "estado_coste": "SIN_PRECIO", "motivo_sin_coste": "Sin precio vigente"},
            {"articulo_id": "ART-2", "nombre_articulo": "Sal", "coste_linea": 0.1,
             "estado_coste": "DISPONIBLE"},
        ]},
    }).detalle_coste_incompleto("PARTIAL")
    no_esc = Details({
        "id": "NO-ESC", "nombre": "Sin escandallo", "estado_coste": "SIN_ESCANDALLO",
        "coste_completo": False, "escandallo": None,
    }).detalle_coste_incompleto("NO-ESC")
    available = Details({
        "id": "OK", "nombre": "Completa", "estado_coste": "DISPONIBLE",
        "coste_completo": True, "escandallo": {"lineas": []},
    }).detalle_coste_incompleto("OK")
    unknown = Details({
        "id": "UNKNOWN", "nombre": "Sin detalle", "estado_coste": "PARCIAL",
        "coste_completo": False, "escandallo": {"lineas": []},
    }).detalle_coste_incompleto("UNKNOWN")
    assert partial["motivos"] == [{
        "tipo": "SIN_PRECIO", "articulo_id": "ART-1", "escandallo_hijo_id": None,
        "nombre": "Patata", "detalle": "Sin precio vigente",
    }]
    assert no_esc == {
        "ok": True, "consulta_economica": "DETAIL_COSTE_INCOMPLETO", "estado": "OK",
        "grounding_scope": "COSTE_INCOMPLETO", "receta_id": "NO-ESC",
        "nombre": "Sin escandallo", "estado_coste": "SIN_ESCANDALLO",
        "coste_completo": False,
        "causa": {"tipo": "SIN_ESCANDALLO", "mensaje": "No existe un escandallo registrado."},
        "datos_reales_modificados": False,
    }
    serialized_no_esc = json.dumps(no_esc)
    assert all(key not in serialized_no_esc for key in (
        "ingredientes", "articulo_id", "precio", "conversion", "pendientes",
    ))
    assert available["coste_completo"] is True and "completo" in available["explicacion"]
    assert unknown["motivos"] == [] and "no expone una causa concreta" in unknown["explicacion"]


def test_detalle_parcial_preserva_conversion_no_disponible_sin_confundir_estados():
    class Details(_AggregateBiblioteca):
        def detalle(self, _identity):
            return {"ok": True, "elaboracion": {
                "id": "CONV", "nombre": "Conversión", "estado_coste": "PARCIAL",
                "coste_completo": False, "escandallo": {"lineas": [{
                    "articulo_id": "ART-CONV", "nombre_articulo": "Producto",
                    "coste_linea": None, "estado_coste": "CONVERSION_NO_DISPONIBLE",
                    "motivo_sin_coste": "Conversión no disponible",
                }]},
            }}

    detail = Details([]).detalle_coste_incompleto("CONV")
    assert detail["estado_coste"] == "PARCIAL"
    assert detail["motivos"][0]["tipo"] == "CONVERSION_NO_DISPONIBLE"
    assert detail["estado_coste"] != "SIN_ESCANDALLO"


def test_resolucion_economica_busca_receta_completa_aunque_no_tenga_escandallo_y_detecta_ambiguedad():
    service = _AggregateBiblioteca([
        _economic("REC601-000001", None, state="SIN_ESCANDALLO", complete=False),
        {**_economic("REC-A", None, state="PARCIAL", complete=False), "nombre": "Salsa roja"},
        {**_economic("REC-B", None, state="PARCIAL", complete=False), "nombre": "Salsa roja picante"},
    ])
    service.summaries[0]["nombre"] = "SALSA DE CAVA"
    resolved = service.resolver_receta_economica("salsa de cava")
    ambiguous = service.resolver_receta_economica("salsa roja")
    assert resolved["estado"] == "RESUELTO" and resolved["receta_id"] == "REC601-000001"
    assert resolved["estado_coste"] == "SIN_ESCANDALLO"
    assert ambiguous["estado"] == "RESUELTO" and ambiguous["receta_id"] == "REC-A"
    partial = service.resolver_receta_economica("roja")
    assert partial["estado"] == "AMBIGUO" and partial["total_coincidencias"] == 2


def _write_fixture(base: Path) -> None:
    db = base / "DATOS" / "db"
    db.mkdir(parents=True)
    recipe = {
        "id": "REC601-000001", "codigo": "SALSA-TOMATE", "nombre": "Salsa de tomate",
        "familia": "Salsas", "categoria": "Salsas", "tipo": "AP", "descripcion": "Base culinaria",
        "numero_raciones": 10, "ingredientes": ["Tomate pera", "Sal"],
        "cantidades": ["2 kg", "20 g"], "elaboracion": "Cocer y triturar.",
        "tiempo_elaboracion": "45 min", "conservacion": "Refrigerado 3 días",
        "alergenos": [], "observaciones": "", "fotografia": "", "estado": "OPERATIVA",
        "version": 2, "creado_en": "2026-01-01", "actualizado_en": "2026-07-30",
        "ficha_tecnica": {"receta": {"elaboracion": "Cocer y triturar."}},
        "completitud": {"porcentaje": 75, "campos_obligatorios_pendientes": ["Producción máxima"]},
        "documentos_pdf": ["fichas/salsa.pdf"], "documentos_word": [], "documentos_fotografias": [],
        "menus_utilizacion": ["Menú verano"], "eventos_utilizacion": ["EVT-1"],
    }
    (db / "biblioteca_recetas_601.json").write_text(
        json.dumps({"version_modelo": "6.0.1", "fichas_tecnicas": [recipe]}), encoding="utf-8",
    )
    (db / "biblioteca_escandallos_601.json").write_text(json.dumps({
        "version_modelo": "6.0.1",
        "escandallos": [{
            "id": "ESC601-000001", "codigo": "ESC-SALSA", "nombre": "Salsa",
            "receta_asociada": {"id": "REC601-000001", "codigo": "SALSA-TOMATE"},
            "estado": "OPERATIVO", "coste_total": 8.5, "coste_por_racion": 0.85,
            "rendimiento_total": 10, "fecha_ultimo_calculo": "2026-07-29",
            "lineas": [
                {"cantidad": 2, "unidad": "kg", "precio_unitario": 4, "coste_linea": 8},
                {"cantidad": 0.02, "unidad": "kg", "precio_unitario": 25, "coste_linea": 0.5},
            ],
        }],
    }), encoding="utf-8")
    (db / "articulos.json").write_text(json.dumps([
        {"codigo": "ART-001", "nombre": "Tomate pera", "precio": 4, "unidad": "kg"},
        {"codigo": "ART-002", "nombre": "Sal", "precio": 0.5, "unidad": "kg"},
    ]), encoding="utf-8")
    (db / "proveedores.json").write_text("[]", encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    invoices = base / "DATOS" / "facturas"
    invoices.mkdir(parents=True)
    (invoices / "historico_precios.json").write_text('{"registros":[]}', encoding="utf-8")


def _write_canonical_fixture(base: Path) -> None:
    db = base / "DATOS" / "db"
    db.mkdir(parents=True)
    (db / "escandallos_canonicos.json").write_text(json.dumps({
        "schema_version": "1.0",
        "escandallos": [
            {
                "receta": {
                    "codigo": "REC-SALSA-ROMESCO",
                    "nombre": "A.P. Salsa romesco",
                    "rendimiento": 12,
                    "unidad_rendimiento": "raciones",
                    "ingredientes": [
                        {
                            "codigo": "ART-001", "articulo_id": "ART-001",
                            "nombre": "Tomate pera", "cantidad": 2, "unidad": "kg",
                            "merma_pct": 5, "precio_unitario": 4,
                        },
                        {"nombre": "Ingrediente heredado", "cantidad": 20, "unidad": "g"},
                    ],
                },
                "coste_total": 8.5,
            },
            {
                "receta": {
                    "codigo": "REC-CREMA-CATALANA",
                    "nombre": "Crema catalana",
                    "rendimiento": 10,
                    "unidad_rendimiento": "raciones",
                    "ingredientes": [{"nombre": "Leche", "cantidad": 1, "unidad": "l"}],
                },
                "coste_total": 0,
            },
        ],
    }, ensure_ascii=False), encoding="utf-8")
    (db / "escandallos.json").write_text(json.dumps([
        {"receta_id": "REC-LEGACY", "nombre": "La fuente legacy no debe duplicarse", "lineas": []},
    ]), encoding="utf-8")
    (db / "articulos.json").write_text(json.dumps([
        {"codigo": "ART-001", "nombre": "Tomate pera", "precio": 4, "unidad": "kg"},
        {"codigo": "ART-002", "nombre": "Leche", "precio": 1, "unidad": "l"},
        {"codigo": "ART-MP", "nombre": "Materia prima no elaborada", "precio": 1, "unidad": "kg"},
    ]), encoding="utf-8")
    (db / "proveedores.json").write_text("[]", encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    invoices = base / "DATOS" / "facturas"
    invoices.mkdir(parents=True)
    (invoices / "historico_precios.json").write_text('{"registros":[]}', encoding="utf-8")


def test_biblioteca_resumen_listado_busqueda_filtros_y_detalle(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    service = BibliotecaCulinariaReadService(tmp_path)
    summary = service.resumen()["biblioteca"]
    assert summary["total_elaboraciones"] == 1
    assert summary["sin_escandallo"] == 0
    listed = service.listar({
        "q": "tomate", "categoria": "Salsas", "tiene_receta": "true",
        "orden": "coste", "direccion": "desc", "page": "1", "page_size": "10",
    })["elaboraciones"]
    assert listed["total"] == 1
    assert listed["items"][0]["tipo"] == "Elaboración"
    detail = service.detalle("REC601-000001")["elaboracion"]
    assert detail["escandallo"]["coste_por_racion"] == 0.801
    assert detail["escandallo"]["coste_total"] == 8.01
    assert detail["escandallo"]["lineas"][0]["origen_precio"] == "catalogo_articulos"
    assert detail["receta"]["ingredientes"][0]["articulo_id"] == "ART-001"
    assert detail["documentos"][0]["tipo"] == "pdf"
    assert "AP" not in json.dumps(detail, ensure_ascii=False)


def test_biblioteca_proyecta_escandallos_canonicos_sin_incluir_articulos(tmp_path: Path) -> None:
    _write_canonical_fixture(tmp_path)
    service = BibliotecaCulinariaReadService(tmp_path)

    summary = service.resumen()["biblioteca"]
    assert summary["total_elaboraciones"] == 2
    assert summary["sin_receta"] == 0
    assert summary["sin_escandallo"] == 0
    assert summary["sin_ficha_tecnica"] == 2

    listed = service.listar({
        "q": "tomate", "tiene_receta": "true", "tiene_escandallo": "true",
        "tiene_ficha_tecnica": "false", "page": "1", "page_size": "1",
    })["elaboraciones"]
    assert listed["total"] == 1
    assert listed["total_pages"] == 1
    assert listed["items"][0]["id"] == "REC-SALSA-ROMESCO"
    assert listed["items"][0]["nombre"] == "Elaboración Salsa romesco"
    assert listed["items"][0]["coste_total"] is None
    assert listed["items"][0]["estado_coste"] == "PARCIAL"
    assert listed["items"][0]["coste_completo"] is False
    assert "sin precio" in listed["items"][0]["motivo_coste_no_disponible"]
    assert listed["items"][0]["tiene_ficha_tecnica"] is False

    all_items = service.listar({})["elaboraciones"]["items"]
    assert {item["id"] for item in all_items} == {
        "REC-SALSA-ROMESCO", "REC-CREMA-CATALANA",
    }
    assert all(item["nombre"] != "Materia prima no elaborada" for item in all_items)
    crema = next(item for item in all_items if item["id"] == "REC-CREMA-CATALANA")
    assert crema["coste_total"] == 1
    assert crema["coste_por_racion"] == 0.1
    assert crema["coste_completo"] is True


def test_biblioteca_detalle_canonico_es_estable_parcial_y_enlaza_articulo_real(tmp_path: Path) -> None:
    _write_canonical_fixture(tmp_path)
    first = BibliotecaCulinariaReadService(tmp_path).detalle("REC-SALSA-ROMESCO")["elaboracion"]
    second = BibliotecaCulinariaReadService(tmp_path).detalle("REC-SALSA-ROMESCO")["elaboracion"]

    assert first["id"] == second["id"] == "REC-SALSA-ROMESCO"
    assert first["tiene_receta"] is True
    assert first["tiene_escandallo"] is True
    assert first["tiene_ficha_tecnica"] is False
    assert first["receta"]["procedimiento"] is None
    assert first["receta"]["ingredientes"][0]["articulo_id"] == "ART-001"
    assert first["receta"]["ingredientes"][0]["codigo"] == "ART-001"
    assert first["receta"]["ingredientes"][0]["nombre_articulo"] == "Tomate pera"
    assert first["receta"]["ingredientes"][0]["unidad_base"] == "kg"
    assert first["receta"]["ingredientes"][0]["cantidad"] == 2.0
    assert first["receta"]["ingredientes"][0]["estado_relacion"] == "relacionado"
    assert first["receta"]["ingredientes"][1]["estado_relacion"] == "sin_relacionar"
    assert [
        line["nombre_original"] for line in first["escandallo"]["lineas"]
    ] == [
        line["nombre_original"] for line in first["receta"]["ingredientes"]
    ]
    assert first["escandallo"]["ingredientes_sin_coste"] == 1
    assert first["escandallo"]["ingredientes_sin_conversion"] == 0
    assert first["escandallo"]["estado_coste"] == "PARCIAL"
    assert first["escandallo"]["coste_total"] is None
    assert first["escandallo"]["coste_total_parcial"] == 8.421053
    assert first["escandallo"]["lineas"][0]["origen_precio"] == "catalogo_articulos"
    assert first["escandallo"]["lineas"][0]["coste_linea"] == 8.421053
    assert first["escandallo"]["lineas"][1]["motivo_sin_coste"] == "Artículo sin relacionar"
    assert first["ficha_tecnica"]["persistida"] is False
    assert first["ficha_tecnica"]["origen"] == "proyeccion_datos_existentes"
    assert first["ficha_tecnica"]["estado"] == "EN_CONSTRUCCION"
    assert "Procedimiento" in first["ficha_tecnica"]["campos_pendientes"]
    assert first["ficha_tecnica"]["ingredientes"] == first["receta"]["ingredientes"]
    assert first["documentos"] == []
    assert first["menus"] == []
    assert first["eventos"] == []
    assert first["produccion"] == {
        "indicaciones": {
            "produccion_minima": None,
            "produccion_maxima": None,
            "personal_recomendado": None,
            "recursos": [],
            "notas": None,
        },
        "ordenes": [],
        "necesidades": [],
        "historial": [],
    }
    assert first["historial"] == []
    assert first["tiene_produccion"] is False
    assert first["tiene_relaciones_menu_evento"] is False
    assert "Ficha técnica en construcción." in first["avisos"]
    assert "A.P" not in json.dumps(first, ensure_ascii=False)


def test_biblioteca_escandallo_reutiliza_precios_conversiones_y_no_extrae_textos(
    tmp_path: Path,
) -> None:
    _write_canonical_fixture(tmp_path)
    db = tmp_path / "DATOS" / "db"
    canonical = json.loads((db / "escandallos_canonicos.json").read_text(encoding="utf-8"))
    canonical["escandallos"][0]["receta"]["ingredientes"] = [
        {"articulo_id": "ART-KG", "nombre": "Harina", "cantidad": 500, "unidad": "g"},
        {"articulo_id": "ART-PACK", "nombre": "Huevos paquete 99,99 €", "cantidad": 1, "unidad": "u"},
        {"articulo_id": "ART-ENV", "nombre": "Mayonesa envase", "cantidad": 0.05, "unidad": "kg"},
        {"articulo_id": "ART-NOUNIT", "nombre": "Producto sin unidad 7,50 €", "cantidad": 1, "unidad": "kg"},
        {"articulo_id": "ART-UNIT", "nombre": "Producto incompatible", "cantidad": 1, "unidad": "kg"},
        {"articulo_id": "ART-L", "nombre": "Aceite", "cantidad": 2, "unidad": "l"},
        {"articulo_id": "ART-ML", "nombre": "Leche", "cantidad": 250, "unidad": "ml"},
        {"articulo_id": "ART-ZERO", "nombre": "Artículo promocional", "cantidad": 1, "unidad": "u"},
        {"nombre": "Artículo no relacionado", "cantidad": 1, "unidad": "u"},
    ]
    (db / "escandallos_canonicos.json").write_text(
        json.dumps(canonical, ensure_ascii=False), encoding="utf-8",
    )
    articles = [
        {"codigo": "ART-KG", "nombre": "Harina", "precio": 2, "unidad": "kg",
         "catalogo_maestro": {"fecha_precio": "2026-07-24"}},
        {"codigo": "ART-PACK", "nombre": "Huevos paquete 99,99 €", "precio": 12, "unidad": "u",
         "catalogo_maestro": {"unidad_compra": "paquete", "cantidad_formato": "6", "unidad_base": "u", "fecha_precio": "2026-07-24"}},
        {"codigo": "ART-ENV", "nombre": "Mayonesa envase", "precio": 11, "unidad": "kg",
         "catalogo_maestro": {"unidad_compra": "envase", "cantidad_formato": "2.2", "unidad_base": "kg", "fecha_precio": "2026-07-24"}},
        {"codigo": "ART-NOUNIT", "nombre": "Producto sin unidad 7,50 €", "precio": 7.5},
        {"codigo": "ART-UNIT", "nombre": "Producto incompatible", "precio": 3, "unidad": "u"},
        {"codigo": "ART-L", "nombre": "Aceite", "precio": 3, "unidad": "l"},
        {"codigo": "ART-ML", "nombre": "Leche", "precio": 2, "unidad": "l"},
        {"codigo": "ART-ZERO", "nombre": "Artículo promocional", "precio": 0, "unidad": "u"},
    ]
    (db / "articulos.json").write_text(json.dumps(articles, ensure_ascii=False), encoding="utf-8")

    esc = BibliotecaCulinariaReadService(tmp_path).detalle("REC-SALSA-ROMESCO")["elaboracion"]["escandallo"]
    lines = esc["lineas"]
    assert lines[0]["precio_unitario"] == 2
    assert lines[0]["precio_original"] == 2
    assert lines[0]["precio_aplicado"] == 2
    assert lines[0]["unidad_precio_original"] == "kg"
    assert lines[0]["unidad_precio_aplicado"] == "kg"
    assert lines[0]["tipo_conversion"] == "metrica"
    assert lines[0]["origen_precio"] == "catalogo_articulos"
    assert lines[0]["factor_conversion"] == 0.001
    assert lines[0]["coste_linea"] == 1
    assert lines[0]["fecha_precio"] == "2026-07-24"
    assert lines[1]["precio_unitario"] is None
    assert lines[1]["precio_original"] is None
    assert lines[1]["unidad_precio_original"] is None
    assert lines[1]["tipo_conversion"] == "directa"
    assert lines[1]["estado_coste"] == "SIN_PRECIO"
    assert lines[1]["motivo_sin_coste"] == "Sin precio vigente"
    assert lines[1]["coste_linea"] is None
    assert lines[2]["precio_unitario"] is None
    assert lines[2]["estado_coste"] == "SIN_PRECIO"
    assert lines[2]["motivo_sin_coste"] == "Sin precio vigente"
    assert lines[2]["coste_linea"] is None
    public_article = ArticulosCatalogReadService(tmp_path).obtener("ART-NOUNIT")["articulo"]
    assert lines[3]["precio_unitario"] == public_article["precio"] == 7.5
    assert lines[3]["origen_precio"] == "catalogo_articulos"
    assert lines[3]["unidad_precio"] == "kg"
    assert lines[3]["unidad_precio_original"] == "kg"
    assert public_article["unidad_base_sugerida"] is True
    assert public_article["estado_unidad_base"] == "SUGERIDA_PENDIENTE_REVISION"
    assert lines[3]["tipo_conversion"] == "directa"
    assert lines[3]["factor_conversion"] == 1
    assert lines[3]["coste_linea"] == 7.5
    assert lines[3]["motivo_sin_coste"] is None
    assert lines[4]["coste_linea"] is None
    assert lines[4]["precio_aplicado"] == 3
    assert lines[4]["unidad_precio_aplicado"] == "u"
    assert lines[4]["tipo_conversion"] == "no_disponible"
    assert lines[4]["motivo_sin_coste"] == "Conversión no disponible"
    assert lines[5]["factor_conversion"] == 1
    assert lines[5]["coste_linea"] == 6
    assert lines[6]["factor_conversion"] == 0.001
    assert lines[6]["coste_linea"] == 0.5
    assert lines[7]["precio_unitario"] is None
    assert lines[7]["coste_linea"] is None
    assert lines[7]["estado_coste"] == "SIN_PRECIO"
    assert lines[8]["estado_coste"] == "ARTICULO_SIN_RELACIONAR"
    for line in lines:
        if line["coste_linea"] is not None:
            assert line["precio_aplicado"] is not None
            assert line["unidad_precio_aplicado"]
            assert line["estado_coste"] == "DISPONIBLE"
            assert line["motivo_sin_coste"] is None
    assert esc["coste_total"] is None
    assert esc["coste_total_parcial"] == 15
    assert esc["coste_por_racion"] is None
    assert esc["ingredientes_sin_conversion"] == 1


def test_biblioteca_detalle_sin_receta_no_inventa_contenido(tmp_path: Path) -> None:
    _write_canonical_fixture(tmp_path)
    path = tmp_path / "DATOS" / "db" / "escandallos_canonicos.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["escandallos"][0]["receta"]["ingredientes"] = []
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    detail = BibliotecaCulinariaReadService(tmp_path).detalle("REC-SALSA-ROMESCO")["elaboracion"]
    assert detail["tiene_receta"] is False
    assert detail["receta"]["ingredientes"] == []
    assert detail["receta"]["pasos"] == []
    assert detail["receta"]["procedimiento"] is None
    assert detail["ficha_tecnica"]["proceso"]["procedimiento"] is None


def test_biblioteca_detalle_separa_canonico_y_propuesta_ia_y_preserva_null(tmp_path: Path) -> None:
    _write_canonical_fixture(tmp_path)
    path = tmp_path / "DATOS" / "db" / "escandallos_canonicos.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    receta = payload["escandallos"][0]["receta"]
    receta["alergenos"] = None
    receta["propuesta_procedimiento_ia"] = "Pochar la cebolla 10 minutos y ligar en frío."
    receta["ingredientes_propuestos_ia"] = ["Sal", "Pimienta", "Tomate pera"]
    receta["alergenos_posibles"] = ["Huevo"]
    receta["conservacion_propuesta_ia"] = "Conservar refrigerado 48 h."
    receta["temperaturas_sugeridas_ia"] = ["Servicio a 65 ºC"]
    receta["tiempos_estimados_ia"] = {"total": "25 min"}
    receta["observaciones_propuestas_ia"] = "Emplatar con hierbas frescas."
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    detail = BibliotecaCulinariaReadService(tmp_path).detalle("REC-SALSA-ROMESCO")["elaboracion"]

    assert detail["receta"]["procedimiento"] is None
    assert detail["alergenos"] is None
    assert "Alérgenos" in detail["pendientes"]
    assert detail["propuestas_ia"]["procedimiento"] == "Pochar la cebolla 10 minutos y ligar en frío."
    assert detail["propuestas_ia"]["conservacion"] == "Conservar refrigerado 48 h."
    assert detail["propuestas_ia"]["alergenos_posibles"] == ["Huevo"]
    assert detail["propuestas_ia"]["temperaturas"] == ["Servicio a 65 ºC"]
    assert detail["propuestas_ia"]["tiempos"] == {"total": "25 min"}
    assert detail["propuestas_ia"]["observaciones"] == "Emplatar con hierbas frescas."
    assert detail["propuestas_ia"]["ingredientes_no_registrados"] == ["Sal", "Pimienta"]
    assert all(
        line["nombre_original"] not in {"Sal", "Pimienta"}
        for line in detail["escandallo"]["lineas"]
    )


def test_biblioteca_sin_datos_parametros_invalidos_y_no_encontrado(tmp_path: Path) -> None:
    service = BibliotecaCulinariaReadService(tmp_path)
    assert service.resumen()["biblioteca"]["estado"] == "sin_datos"
    assert service.listar({})["elaboraciones"]["items"] == []
    assert service.listar({"page_size": "101"})["error"]["status"] == 400
    assert service.listar({"tiene_receta": "quizas"})["error"]["status"] == 400
    assert service.detalle("NO-EXISTE")["error"]["status"] == 404


def test_http_biblioteca_contratos_publicos(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    client = TestClient(create_app(HostAIPlatformAPI(base_dir=tmp_path)))
    assert client.get("/api/v1/biblioteca").json()["biblioteca"]["total_elaboraciones"] == 1
    listed = client.get("/api/v1/biblioteca/elaboraciones?q=salsa")
    assert listed.status_code == 200
    assert listed.json()["elaboraciones"]["total"] == 1
    detail = client.get("/api/v1/biblioteca/elaboraciones/REC601-000001")
    assert detail.status_code == 200
    assert detail.json()["elaboracion"]["nombre"] == "Salsa de tomate"
    assert client.get("/api/v1/biblioteca/elaboraciones/NO-EXISTE").status_code == 404


def test_http_biblioteca_publica_fuente_canonica_real(tmp_path: Path) -> None:
    _write_canonical_fixture(tmp_path)
    client = TestClient(create_app(HostAIPlatformAPI(base_dir=tmp_path)))

    response = client.get("/api/v1/biblioteca/elaboraciones?q=romesco")
    assert response.status_code == 200
    assert response.json()["elaboraciones"]["items"][0]["id"] == "REC-SALSA-ROMESCO"

    detail = client.get("/api/v1/biblioteca/elaboraciones/REC-SALSA-ROMESCO")
    assert detail.status_code == 200
    assert detail.json()["elaboracion"]["receta"]["ingredientes"][0]["articulo_id"] == "ART-001"
