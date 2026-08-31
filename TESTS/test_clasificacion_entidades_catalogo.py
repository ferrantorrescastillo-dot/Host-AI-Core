import json

from SERVICIOS.clasificacion_entidad_catalogo import (
    ARTICULO_COMPRADO, ELABORACION_INTERNA, PRODUCTO_VENDIBLE,
    SUBELABORACION, AuditorClasificacionLegada, ClasificadorImportacionEntidades, origen_coste,
    requiere_precio_compra,
)
from SERVICIOS.precio_referencia_web_service import PrecioReferenciaWebService
from SERVICIOS.precio_referencias_import_service import PrecioReferenciasImportService
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.reclasificacion_entidad_catalogo_service import ReclasificacionEntidadCatalogoService


def _service(tmp_path, articles, recipes=None):
    db = tmp_path / "DATOS" / "db"; db.mkdir(parents=True)
    (db / "articulos.json").write_text(json.dumps(articles), encoding="utf-8")
    (db / "escandallos_canonicos.json").write_text(json.dumps({"escandallos": recipes or []}), encoding="utf-8")
    return PrecioReferenciasImportService(tmp_path, PrecioReferenciaWebService(tmp_path)), db


def test_only_purchasable_entities_without_price_are_exported(tmp_path) -> None:
    service, _ = _service(tmp_path, [
        {"codigo": "ART-CORVINA", "nombre": "Corvina", "precio": None, "tipo_entidad": ARTICULO_COMPRADO},
        {"codigo": "ART-CEVICHE", "nombre": "Ceviche", "precio": None, "tipo_entidad": ELABORACION_INTERNA, "elaboracion_id": "REC-CEVICHE"},
        {"codigo": "ART-FONDO", "nombre": "Fondo", "precio": None, "tipo_entidad": SUBELABORACION, "elaboracion_id": "REC-FONDO"},
    ])
    missing = service.missing_articles(); exported = service.export_text()
    assert [row["article_id"] for row in missing["articulos"]] == ["ART-CORVINA"]
    assert {row["article_id"] for row in missing["costes_derivados"]} == {"ART-CEVICHE", "ART-FONDO"}
    assert all(row["estado"] == "ESCANDALLO_PENDIENTE" for row in missing["costes_derivados"])
    assert "ART-CORVINA" in exported["texto"]
    assert "ART-CEVICHE" not in exported["texto"] and "ART-FONDO" not in exported["texto"]


def test_internal_elaboration_with_complete_costing_reports_derived_cost(tmp_path) -> None:
    service, _ = _service(tmp_path, [
        {"codigo": "ART-BASE", "nombre": "Base comprada", "precio": 2.0, "unidad_base": "kg"},
        {"codigo": "ART-ELAB", "nombre": "Elaboración", "precio": None, "tipo_entidad": ELABORACION_INTERNA, "elaboracion_id": "REC-ELAB"},
    ], [{"receta": {
        "codigo": "REC-ELAB", "nombre": "Elaboración", "rendimiento": 2,
        "unidad_rendimiento": "u", "ingredientes": [{
            "codigo": "ART-BASE", "articulo_id": "ART-BASE", "nombre": "Base comprada",
            "cantidad": 1, "unidad": "kg", "merma_pct": 0,
        }],
    }}])

    result = service.missing_articles()

    assert result["articulos"] == []
    assert result["costes_derivados"][0]["estado"] == "COSTE_DERIVADO_ESCANDALLO"
    assert result["costes_derivados"][0]["coste_total"] == 2.0
    assert result["costes_derivados"][0]["coste_por_racion"] == 1.0


def test_same_name_without_explicit_relation_is_not_automatically_linked(tmp_path) -> None:
    service, db = _service(tmp_path,
        [{"codigo": "ART000327", "nombre": "Ceviche de corvina", "precio": None, "origen": "excel"}],
        [{"receta": {"codigo": "REC-EXCEL-A763F10EE4", "nombre": "Ceviche de corvina", "rendimiento": 58, "unidad_rendimiento": "u", "ingredientes": []}}],
    )
    before = (db / "articulos.json").read_bytes()
    assert service.missing_articles()["articulos"][0]["article_id"] == "ART000327"
    candidate = service.migration_candidates()["candidatos"][0]
    assert candidate["coincidencias"][0]["elaboracion_id"] == "REC-EXCEL-A763F10EE4"
    assert candidate["estado"] == "REQUIERE_REVISION"
    assert (db / "articulos.json").read_bytes() == before
    assert "elaboracion_id" not in json.loads(before)[0]


def test_migration_preview_preserves_legacy_price_as_unclassified_data(tmp_path) -> None:
    service, db = _service(tmp_path,
        [{"codigo": "ART-LEGACY", "nombre": "Salsa base", "precio": 12.5, "origen": "excel", "observaciones": "elaboración"}],
        [{"receta": {"codigo": "REC-SALSA", "nombre": "Salsa base", "ingredientes": []}}],
    )
    before = (db / "articulos.json").read_bytes(); result = service.migration_candidates()
    assert result["requiere_preview_confirm"] is True and result["datos_reales_modificados"] is False
    assert result["candidatos"][0]["acciones_permitidas"] == ["VINCULAR_COMO_ELABORACION", "MANTENER_COMO_ARTICULO_COMPRADO", "REVISAR"]
    assert (db / "articulos.json").read_bytes() == before
    assert json.loads(before)[0]["precio"] == 12.5


def test_cost_origin_is_structured_and_never_copies_recipe_cost() -> None:
    elaboration = {"tipo_entidad": ELABORACION_INTERNA, "elaboracion_id": "REC-1", "precio": None}
    sellable_from_recipe = {"tipo_entidad": PRODUCTO_VENDIBLE, "elaboracion_id": "REC-1", "precio": 19.0}
    bought_sellable = {"tipo_entidad": PRODUCTO_VENDIBLE, "precio": None}
    assert requiere_precio_compra(elaboration) is False
    assert origen_coste(elaboration) == "COSTE_DERIVADO_ELABORACION"
    assert requiere_precio_compra(sellable_from_recipe) is False
    assert sellable_from_recipe["precio"] == 19.0
    assert requiere_precio_compra(bought_sellable) is True


def test_candidate_auditor_is_read_only(tmp_path) -> None:
    _, db = _service(tmp_path,
        [{"codigo": "ART-1", "nombre": "Fondo oscuro", "precio": None, "origen": "excel"}],
        [{"receta": {"codigo": "REC-1", "nombre": "Fondo oscuro"}}],
    )
    before = (db / "articulos.json").read_bytes()
    result = AuditorClasificacionLegada(tmp_path).candidatos()
    assert result["total"] == 1 and result["datos_reales_modificados"] is False
    assert (db / "articulos.json").read_bytes() == before


def test_ceviche_preview_confirm_idempotency_and_new_missing_price_read(tmp_path) -> None:
    price_service, db = _service(tmp_path,
        [{"codigo": "ART-CEVICHE", "nombre": "Ceviche de corvina", "precio": None, "origen": "excel", "proveedor": "LEGACY"}],
        [{"receta": {"codigo": "REC-CEVICHE", "nombre": "Ceviche de corvina", "rendimiento": 1, "unidad_rendimiento": "u", "ingredientes": []}}],
    )
    context = AuthorizedExecutionContext("REQ-1", "CHEF", "LOCAL", ("chef",), frozenset({"articulos:write"}))
    service = ReclasificacionEntidadCatalogoService(tmp_path)
    rows = [{"article_id": "ART-CEVICHE", "tipo_entidad": "ELABORACION_INTERNA", "elaboracion_id": "REC-CEVICHE"}]
    before = (db / "articulos.json").read_bytes()
    preview = service.preview(rows, context)
    assert (db / "articulos.json").read_bytes() == before
    first = service.confirm(rows, preview["preview_token"], context)
    second_preview = service.preview(rows, context)
    second = service.confirm(rows, second_preview["preview_token"], context)
    stored = json.loads((db / "articulos.json").read_text(encoding="utf-8"))[0]
    assert first["writes_logicos"] == 1 and first["idempotente"] is False
    assert second["writes_logicos"] == 0 and second["idempotente"] is True
    assert stored["tipo_entidad"] == "ELABORACION_INTERNA"
    assert stored["elaboracion_id"] == "REC-CEVICHE"
    assert stored["origen_coste"] == "COSTE_DERIVADO_ELABORACION"
    assert stored["precio"] is None and stored["proveedor"] == "LEGACY"
    assert price_service.missing_articles()["articulos"] == []


def test_mass_import_analysis_classifies_deduplicates_and_does_not_write() -> None:
    recipes = []
    for index in range(40):
        ingredients = [{"nombre": "Nata"}, {"nombre": "Cebolla"}, {"nombre": f"Materia {index % 10}"}]
        if index: ingredients.append({"nombre": "Fondo oscuro"})
        recipes.append({"nombre": "Fondo oscuro" if index == 0 else f"Receta {index}", "ingredientes": ingredients})
    result = ClasificadorImportacionEntidades().analizar(recipes)
    assert result["resumen"]["recetas_detectadas"] == 40
    assert result["resumen"]["articulos_comprados_unicos"] == 12
    assert result["resumen"]["subelaboraciones"] == 1
    assert result["subelaboraciones"][0]["nombre"] == "Fondo oscuro"
    assert result["datos_reales_modificados"] is False
    assert len([row for row in result["articulos_comprados"] if row["nombre"] == "Nata"]) == 1
