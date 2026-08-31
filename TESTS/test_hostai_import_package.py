from __future__ import annotations

import json
import base64
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from MODELOS.hostai_import_package import HostAIImportPackageError, hostai_import_package_json_schema
from SERVICIOS.hostai_import_package_adapter import PreparedImportPackageAdapter
from SERVICIOS.importador_inteligente_biblioteca import ImportDocumentService
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601


def _package(**overrides):
    value = {
        "schema": "hostai.import.package", "version": "0.1",
        "metadata": {"source": "fixture", "generator": "test"},
        "recipes": [{
            "source_id": "EXT-REC-1", "name": "Salsa de naranja",
            "ingredients": [{"name": "Naranja", "quantity": 1, "unit": "kg", "observed": "NARANJA"}],
            "procedure": ["Reducir"], "yield": 1, "yield_unit": "kg",
            "occurrences": [
                {"sheet": "A", "row": 3}, {"sheet": "B", "row": 9},
                {"sheet": "C", "row": 4}, {"sheet": "D", "row": 12},
            ],
        }],
        "articles": [{"source_code": "EXT-A-1", "name": "Naranja", "unit": "kg",
            "interpretation": {"classification": "ARTICULO_COMPRADO_CANDIDATE"}, "document_price": {
            "value": 1.25, "currency": "EUR", "format": "caja 5 kg", "unit": "kg", "context": "tarifa",
        }}],
        "suppliers": [], "menus": [], "relations": [], "ambiguities": [], "variant_groups": [],
    }
    value.update(overrides)
    return value


def test_contract_accepts_schema_01_and_ignores_unknown_fields():
    package = PreparedImportPackageAdapter.validate({**_package(), "future_hint": True})
    assert package.schema == "hostai.import.package"
    assert package.version == "0.1"
    assert package.warnings == ("Campo desconocido ignorado: future_hint",)


def test_official_schema_and_adapter_both_require_name_for_named_entities():
    schema = hostai_import_package_json_schema()
    for collection in ("recipes", "articles", "suppliers", "menus"):
        assert schema["properties"][collection]["items"]["required"] == ["name"]
    invalid = _package(suppliers=[{"name_observed": "SARDA"}])
    with pytest.raises(HostAIImportPackageError, match=r"suppliers\[0\] requiere name"):
        PreparedImportPackageAdapter.validate(invalid)


def test_generator_metadata_does_not_change_validation_or_adapter_result():
    analyses = []
    for generator_name in ("ChatGPT", "Claude", "Gemini", "Otra IA"):
        package = _package(metadata={
            "source": "fixture",
            "extractor": {"name": generator_name, "version": "test", "generated_at": "2026-08-28T00:00:00Z"},
        })
        validated = PreparedImportPackageAdapter.validate(package)
        analyses.append(PreparedImportPackageAdapter().analyze({"hostai_import_package": package}))
        assert validated.schema == "hostai.import.package"
        assert validated.version == "0.1"

    semantic_results = [{
        key: analysis[key]
        for key in ("recetas", "articulos", "menus", "relaciones", "ambiguities", "variant_groups", "coste_ia")
        if key in analysis
    } for analysis in analyses]
    assert semantic_results[1:] == [semantic_results[0]] * 3
    assert [item["nombre"] for item in analyses[0]["recetas"]] == ["Salsa de naranja"]
    assert [item["nombre"] for item in analyses[0]["articulos"]] == ["Naranja"]
    assert analyses[0]["coste_ia"]["llamadas"] == 0


def test_orphan_numeric_cell_without_quantity_is_not_projected_as_ingredient():
    package = _package(recipes=[{
        "name": "Tabla de queso con pan de cristal",
        "ingredients": [
            {"name": "Queso Altejo", "quantity": 0.070, "unit": "kg", "provenance": {"sheet": "M.P Aperitivos", "source_row": 27}},
            {"name": "25", "quantity": None, "unit": None, "provenance": {"sheet": "M.P Aperitivos", "source_row": 39}},
        ],
        "procedure": [],
    }])

    analysis = PreparedImportPackageAdapter().analyze({"hostai_import_package": package})

    ingredients = analysis["recetas"][0]["ingredientes_estructurados"]
    assert [item["nombre_original"] for item in ingredients] == ["Queso Altejo"]
    assert analysis["resumen"]["ingredientes_detectados"] == 1


@pytest.mark.parametrize("change", [
    {"schema": "otro.schema"}, {"version": "9.0"}, {"recipes": "no-lista"},
])
def test_contract_rejects_invalid_schema_version_or_shape(change):
    with pytest.raises(HostAIImportPackageError):
        PreparedImportPackageAdapter.validate({**_package(), **change})


@pytest.mark.parametrize("unsafe", [
    {"stock": 10}, {"article_id": "ART-INVENTADO"}, {"permissions": ["admin"]},
    {"purchases": [{"id": "P-1"}]},
])
def test_contract_rejects_operational_authority_at_any_depth(unsafe):
    package = _package()
    package["recipes"][0]["interpretation"] = unsafe
    with pytest.raises(HostAIImportPackageError, match="autoridad operativa"):
        PreparedImportPackageAdapter.validate(package)


def test_adapter_keeps_context_menu_outside_recipes_and_consolidates_occurrences():
    analysis = PreparedImportPackageAdapter().analyze({"hostai_import_package": _package(
        menus=[
            {"name": "TAPA", "kind": "CONTEXT", "items": ["Salsa de naranja"]},
            {"name": "Menú degustación", "kind": "MENU", "items": ["Salsa de naranja"]},
        ]
    )})
    assert [item["nombre"] for item in analysis["recetas"]] == ["Salsa de naranja"]
    assert len(analysis["recetas"][0]["bloques_origen"]) == 4
    assert [item["tipo"] for item in analysis["menus"]] == ["CONTEXT", "MENU"]


def test_variant_group_preserves_structurally_distinct_versions_for_review():
    analysis = PreparedImportPackageAdapter().analyze({"hostai_import_package": _package(
        recipes=[], variant_groups=[{
            "name": "Salsa romesco", "versions": [
                {"ingredients": [{"name": "Almendra", "quantity": 1, "unit": "kg"}]},
                {"ingredients": [{"name": "Avellana", "quantity": 1, "unit": "kg"}]},
            ],
        }]
    )})
    assert len(analysis["recetas"]) == 2
    assert all(item["posible_variante"] for item in analysis["recetas"])
    assert {item["ingredientes_estructurados"][0]["nombre_original"] for item in analysis["recetas"]} == {"Almendra", "Avellana"}


def test_identity_and_variant_decisions_persist_in_canonical_memory_draft_without_domain_write(tmp_path: Path):
    package = _package(recipes=[], articles=[], variant_groups=[{
        "name": "Patatas Bravas", "versions": [
            {"ingredients": [{"name": "Patata", "quantity": 1, "unit": "kg"}]},
            {"ingredients": [{"name": "Patata", "quantity": 2, "unit": "kg"}]},
        ],
    }])
    service = ImportDocumentService(tmp_path)
    session = service.import_document({"hostai_import_package": package})["importacion"]
    draft = session["borrador"]
    group_id = draft["variant_decisions"][0]["group_id"]
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}

    recipes = [dict(item) for item in draft["recipes"]]
    recipes[0]["identity_decision"] = "RECETA_NUEVA"
    recipes[0]["proposed_action"] = "CREAR_RECETA"
    updated = service.update_draft(session["documento"]["id"], {
        "draft_version": draft["draft_version"], "recipes": recipes,
        "variant_decisions": [{"group_id": group_id, "decision": "RECETAS_DIFERENTES"}],
    })

    assert updated["ok"] is True
    reread = service.get_draft(session["documento"]["id"])["borrador"]
    assert reread["recipes"][0]["identity_decision"] == "RECETA_NUEVA"
    assert reread["variant_decisions"] == [{"group_id": group_id, "decision": "RECETAS_DIFERENTES"}]
    assert service.get_import(session["documento"]["id"])["importacion"]["resolucion_identidad"]["variantes"]["grupos_requieren_decision"] == 0
    assert {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before


def test_batch_review_decisions_persist_and_recalculate_without_domain_write(tmp_path: Path):
    articles = [{
        "name": f"A.P pendiente {index}",
        "interpretation": {"classification": "RECETA_O_ELABORACION_EXISTENTE_CANDIDATE"},
    } for index in range(54)]
    recipes = [{
        "name": f"Receta lote {index}", "ingredients": [], "procedure": ["Preparar"], "yield": 1,
    } for index in range(3)]
    variants = [{
        "name": f"Variante lote {index}", "versions": [
            {"ingredients": [{"name": "Patata", "quantity": 1, "unit": "kg"}]},
            {"ingredients": [{"name": "Patata", "quantity": 2, "unit": "kg"}]},
        ],
    } for index in range(2)]
    service = ImportDocumentService(tmp_path)
    session = service.import_document({"hostai_import_package": _package(
        recipes=recipes, articles=articles, variant_groups=variants,
    )})["importacion"]
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    draft = session["borrador"]

    decisions = [dict(item) for item in draft["article_decisions"]]
    for index, item in enumerate(decisions):
        item["decision"] = "IGNORAR" if index < 41 else "ES_ELABORACION"
    recipes_draft = [{**item, "identity_decision": "RECETA_NUEVA", "proposed_action": "CREAR_RECETA"}
                     for item in draft["recipes"]]
    variants_draft = [{**item, "decision": "RECETAS_DIFERENTES"} for item in draft["variant_decisions"]]
    first = service.update_draft(session["documento"]["id"], {
        "draft_version": draft["draft_version"], "recipes": recipes_draft,
        "variant_decisions": variants_draft, "article_decisions": decisions,
    })
    current = first["borrador"]
    assert sum(item["decision"] == "IGNORAR" for item in current["article_decisions"]) == 41
    assert sum(item["decision"] == "ES_ELABORACION" for item in current["article_decisions"]) == 13
    assert all(item["identity_decision"] == "RECETA_NUEVA" for item in current["recipes"][:3])
    assert all(item["decision"] == "RECETAS_DIFERENTES" for item in current["variant_decisions"])

    restored = [
        {**item, "decision": "PENDIENTE"} if index in range(36, 41) else item
        for index, item in enumerate(current["article_decisions"])
    ]
    second = service.update_draft(session["documento"]["id"], {
        "draft_version": current["draft_version"], "recipes": current["recipes"],
        "variant_decisions": current["variant_decisions"], "article_decisions": restored,
    })
    reread = service.get_import(session["documento"]["id"])["importacion"]
    assert sum(item["decision"] == "IGNORAR" for item in reread["borrador"]["article_decisions"]) == 36
    assert sum(item["decision"] == "PENDIENTE" for item in reread["borrador"]["article_decisions"]) == 5
    assert reread["preview_global"]["contadores"]["articulos_ignorados"] == 36
    assert reread["preview_global"]["contadores"]["articulos_reclasificados_elaboracion"] == 13
    assert second["datos_reales_modificados"] is False
    assert {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before


def test_current_draft_preview_replaces_original_boronat_projection_and_exposes_menus(tmp_path: Path):
    recipes = [{
        "source_id": f"REC-{index}", "name": f"Receta Boronat {index}",
        "ingredients": [{"name": "Ingrediente seguro", "quantity": 1, "unit": "kg"}],
        "procedure": ["Preparar"], "yield": 1,
    } for index in range(46)]
    articles = [{
        "source_code": f"ART-{index}", "name": f"Registro Boronat {index}",
        "interpretation": {"classification": "RECETA_O_ELABORACION_EXISTENTE_CANDIDATE"},
    } for index in range(314)]
    menus = [{"name": f"Menú Boronat {index}", "items": []} for index in range(15)]
    service = ImportDocumentService(tmp_path)
    session = service.import_document({"hostai_import_package": _package(
        recipes=recipes, articles=articles, menus=menus,
    )})["importacion"]

    # El fixture reproduce el catálogo canónico consolidado que llega a revisión: 16 de 314 registros fuente.
    draft = session["borrador"]
    draft["catalogo"]["articulos"] = draft["catalogo"]["articulos"][:16]
    draft["catalogo"]["relaciones"] = []
    draft["article_decisions"] = draft["article_decisions"][:16]
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}

    article_decisions = [
        {**item, "decision": "ES_ELABORACION" if index < 13 else "PENDIENTE"}
        for index, item in enumerate(draft["article_decisions"])
    ]
    identity = [
        ("VARIANTE", "CREAR_RECETA"), ("VARIANTE", "CREAR_RECETA"),
        ("MISMA_RECETA", "REUTILIZAR_EXISTENTE"),
        ("RECETA_NUEVA", "CREAR_RECETA"), ("RECETA_NUEVA", "CREAR_RECETA"),
        ("RECETA_NUEVA", "CREAR_RECETA"), ("PENDIENTE", "REQUIERE_REVISION"),
    ]
    revised_recipes = [dict(item) for item in draft["recipes"]]
    for index, (decision, action) in enumerate(identity):
        revised_recipes[index]["identity_decision"] = decision
        revised_recipes[index]["proposed_action"] = action

    updated = service.update_draft(session["documento"]["id"], {
        "draft_version": draft["draft_version"], "recipes": revised_recipes,
        "variant_decisions": draft.get("variant_decisions", []),
        "article_decisions": article_decisions,
    })
    preview = updated["preview_global"]
    assert preview["contadores"]["articulos_reclasificados_elaboracion"] == 13
    assert preview["contadores"]["articulos_requieren_revision"] == 3
    assert preview["contadores"]["recetas_requieren_revision"] == 2
    assert preview["contadores"]["pendientes"] == 20
    assert preview["contadores"]["pendientes_desglose"] == {
        "identidad_receta": 2, "articulo": 3, "relacion": 0,
        "proveedor": 0, "documentacion": 0, "menu": 15, "otro": 0,
    }
    assert len(updated["borrador"]["menus"]) == 15
    assert preview["contadores"]["menus_recibidos"] == 15
    assert preview["contadores"]["menus_pendientes"] == 15
    assert len(preview["menus"]["pendientes"]) == 15
    assert preview["draft_version"] == updated["borrador"]["draft_version"]
    assert len(preview["draft_fingerprint"]) == 64
    assert any(issue["code"] == "PREVIEW_OBSOLETO" for issue in service.confirmations.preflight(
        service._sessions[session["documento"]["id"]], updated["borrador"]["version"], "obsoleto",
    ))
    assert not service.confirmations.preflight(
        service._sessions[session["documento"]["id"]], updated["borrador"]["version"],
        preview["draft_fingerprint"],
    )
    assert {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before


def test_confirm_projection_excludes_pending_recipe_and_articles_without_real_write(tmp_path: Path):
    RepositorioProductosMaestro601(tmp_path).crear_producto({"nombre": "Naranja", "unidad_base": "kg"})
    recipes = [
        {"name": "Receta segura", "ingredients": [{"name": "Naranja", "quantity": 1, "unit": "kg"}], "procedure": ["Preparar"], "yield": 1},
        {"name": "Receta pendiente", "ingredients": [{"name": "Naranja", "quantity": 1, "unit": "kg"}], "procedure": ["Preparar"], "yield": 1},
    ]
    articles = [{
        "name": f"Posible elaboración {index}",
        "interpretation": {"classification": "RECETA_O_ELABORACION_EXISTENTE_CANDIDATE"},
    } for index in range(16)]
    service = ImportDocumentService(tmp_path)
    session = service.import_document({"hostai_import_package": _package(recipes=recipes, articles=articles)})["importacion"]
    draft = session["borrador"]
    revised_recipes = [dict(item) for item in draft["recipes"]]
    revised_recipes[0].update(identity_decision="RECETA_NUEVA", proposed_action="CREAR_RECETA")
    revised_recipes[1].update(identity_decision="PENDIENTE", proposed_action="REQUIERE_REVISION")
    decisions = [
        {**item, "decision": "ES_ELABORACION" if index < 13 else "PENDIENTE"}
        for index, item in enumerate(draft["article_decisions"])
    ]
    updated = service.update_draft(session["documento"]["id"], {
        "draft_version": draft["draft_version"], "recipes": revised_recipes,
        "variant_decisions": [], "article_decisions": decisions,
    })
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    changes, actions, entities = service.confirmations._prepare_domain_changes(
        service._sessions[session["documento"]["id"]]
    )
    assert changes
    assert any(item["tipo"] == "CREAR_RECETA" for item in actions)
    assert not any(item.get("nombre") == "Receta pendiente" for item in entities)
    assert not any(item["tipo"] == "CREAR_ARTICULO" for item in actions)
    assert updated["preview_global"]["contadores"]["articulos_reclasificados_elaboracion"] == 13
    assert updated["preview_global"]["contadores"]["articulos_requieren_revision"] == 3
    assert {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before


def test_recipe_reuse_keeps_canonical_id_and_never_falls_back_to_name(tmp_path: Path):
    created = RepositorioBibliotecaRecetas601(tmp_path).crear_incompleta_desde_importacion({
        "nombre": "Receta canónica X", "ingredientes": ["Naranja"],
        "cantidades": ["1 kg"], "numero_raciones": 1,
    })
    canonical = created["receta"]
    service = ImportDocumentService(tmp_path)
    session = service.import_document({"hostai_import_package": _package()})["importacion"]
    draft = session["borrador"]
    draft["recipes"][0]["duplicate_candidates"] = [
        {"id": canonical["id"], "nombre": canonical["nombre"], "tipo": "RECETA_CANONICA"}
    ]
    recipes = [dict(item) for item in draft["recipes"]]
    recipes[0].update(
        title="Un nombre que no coincide",
        identity_decision="MISMA_RECETA",
        proposed_action="REUTILIZAR_EXISTENTE",
    )

    updated = service.update_draft(session["documento"]["id"], {
        "draft_version": draft["draft_version"], "recipes": recipes,
        "variant_decisions": draft.get("variant_decisions", []),
        "article_decisions": draft.get("article_decisions", []),
    })
    _changes, actions, _entities = service.confirmations._prepare_domain_changes(
        service._sessions[session["documento"]["id"]]
    )

    assert updated["borrador"]["recipes"][0]["proposed_action"] == "REUTILIZAR_EXISTENTE"
    assert {item["id"] for item in actions if item["tipo"] == "REUTILIZAR_RECETA"} == {canonical["id"]}


def test_stale_or_legacy_recipe_candidate_returns_to_pending_before_preview(tmp_path: Path):
    service = ImportDocumentService(tmp_path)
    session = service.import_document({"hostai_import_package": _package()})["importacion"]
    draft = session["borrador"]
    draft["recipes"][0]["duplicate_candidates"] = [{
        "id": "REC-EXCEL-STALE", "nombre": "Solo escandallo",
        "tipo": "ESCANDALLO_SIN_RECETA_CANONICA",
    }]
    recipes = [dict(item) for item in draft["recipes"]]
    recipes[0].update(
        identity_decision="MISMA_RECETA",
        proposed_action="REUTILIZAR_EXISTENTE",
    )

    updated = service.update_draft(session["documento"]["id"], {
        "draft_version": draft["draft_version"], "recipes": recipes,
        "variant_decisions": draft.get("variant_decisions", []),
        "article_decisions": draft.get("article_decisions", []),
    })
    recipe = updated["borrador"]["recipes"][0]

    assert recipe["identity_decision"] == "PENDIENTE"
    assert recipe["proposed_action"] == "REQUIERE_REVISION"
    assert updated["preview_global"]["contadores"]["recetas_requieren_revision"] == 1


def test_fifteen_safe_menus_project_and_new_recipe_dependency_uses_canonical_id(tmp_path: Path):
    menus = [{
        "name": f"Menú seguro {index}", "kind": "MENU",
        "items": [{"nombre": "Salsa de naranja", "seccion": "Salsas", "cantidad_origen": 1}],
    } for index in range(15)]
    service = ImportDocumentService(tmp_path)
    session = service.import_document({"hostai_import_package": _package(menus=menus)})["importacion"]
    preview = session["preview_global"]
    assert len(session["borrador"]["menus"]) == 15
    assert preview["contadores"]["menus_recibidos"] == 15
    assert preview["contadores"]["menus_crear"] == 15
    assert preview["contadores"]["menus_reutilizar"] == 0
    assert preview["contadores"]["menus_pendientes"] == 0
    assert preview["contadores"]["menu_lineas_resueltas"] == 15
    assert all(item["lineas"][0]["futura"] for item in preview["menus"]["crear"])

    stock = tmp_path / "DATOS/db/stock_lotes.json"
    stock.parent.mkdir(parents=True, exist_ok=True)
    stock.write_text('{"fixture":true}', encoding="utf-8")
    stock_before = stock.read_bytes()
    confirmed = service.confirm(session["documento"]["id"], {
        "draft_version": session["borrador"]["version"],
        "preview_fingerprint": preview["draft_fingerprint"],
        "usuario": "test", "confirmacion": "CONFIRMAR",
    })
    assert confirmed["ok"] is True
    assert stock.read_bytes() == stock_before
    stored_recipe = RepositorioBibliotecaRecetas601(tmp_path).listar()[0]
    menus_stored = json.loads((tmp_path / "DATOS/db/menus.json").read_text(encoding="utf-8"))
    assert len(menus_stored) == 15
    assert all(
        line["referencia"] == stored_recipe["id"]
        for menu in menus_stored
        for lines in menu["composicion"].values()
        for line in lines
    )
    verification = confirmed["resultado"]["verificacion_post_write"]
    assert verification["total"] == 15
    assert all(item["referencias"] == [stored_recipe["id"]] for item in verification["menus"])


def test_existing_menu_is_reused_and_reimport_does_not_duplicate(tmp_path: Path):
    package = _package(menus=[{
        "name": "Menú idempotente", "kind": "MENU",
        "items": [{"nombre": "Salsa de naranja", "seccion": "Salsas", "cantidad_origen": 1}],
    }])
    first_service = ImportDocumentService(tmp_path)
    first = first_service.import_document({"hostai_import_package": package})["importacion"]
    assert first_service.confirm(first["documento"]["id"], {
        "draft_version": first["borrador"]["version"], "usuario": "test", "confirmacion": "CONFIRMAR",
    })["ok"] is True
    second_service = ImportDocumentService(tmp_path)
    second = second_service.import_document({"hostai_import_package": package})["importacion"]
    assert second["preview_global"]["contadores"]["menus_reutilizar"] == 1
    assert second_service.confirm(second["documento"]["id"], {
        "draft_version": second["borrador"]["version"], "usuario": "test", "confirmacion": "CONFIRMAR",
    })["ok"] is True
    stored = json.loads((tmp_path / "DATOS/db/menus.json").read_text(encoding="utf-8"))
    assert len(stored) == 1


def test_ambiguous_or_structurally_distinct_menus_stay_pending_without_invention(tmp_path: Path):
    package = _package(menus=[
        {"name": "Dos ensaladas", "kind": "MENU", "items": [{"nombre": "Ensalada verde", "seccion": "Entrantes"}]},
        {"name": "Dos ensaladas", "kind": "MENU", "items": [{"nombre": "Ensalada de tomate", "seccion": "Entrantes"}]},
    ])
    service = ImportDocumentService(tmp_path)
    session = service.import_document({"hostai_import_package": package})["importacion"]
    assert session["preview_global"]["contadores"]["menus_pendientes"] == 2
    assert session["preview_global"]["contadores"]["menus_crear"] == 0
    assert all(item["lineas_pendientes"] == 1 for item in session["preview_global"]["menus"]["pendientes"])
    changes, actions, _entities = service.confirmations._prepare_domain_changes(service._sessions[session["documento"]["id"]])
    assert "DATOS/db/menus.json" not in changes
    assert not any(action["tipo"] == "CREAR_MENU" for action in actions)


def test_clean_package_does_not_regenerate_removed_beer_line(tmp_path: Path):
    package = _package(menus=[{
        "name": "Menú limpio", "kind": "MENU",
        "items": [{"nombre": "Salsa de naranja", "seccion": "Salsas"}],
    }])
    session = ImportDocumentService(tmp_path).import_document({"hostai_import_package": package})["importacion"]
    serialized = json.dumps({"draft": session["borrador"]["menus"], "preview": session["preview_global"]["menus"]}, ensure_ascii=False)
    assert "Caña de cerveza" not in serialized


def test_menu_failure_rolls_back_recipe_and_menu_domain_writes(tmp_path: Path, monkeypatch):
    package = _package(menus=[{
        "name": "Menú transaccional", "kind": "MENU",
        "items": [{"nombre": "Salsa de naranja", "seccion": "Salsas"}],
    }])
    service = ImportDocumentService(tmp_path)
    session = service.import_document({"hostai_import_package": package})["importacion"]

    def fail_menu(*_args, **_kwargs):
        raise RuntimeError("fallo de menú simulado")

    monkeypatch.setattr("SERVICIOS.menu_importacion_biblioteca.BibliotecaMenus601.nuevo_menu", fail_menu)
    result = service.confirm(session["documento"]["id"], {
        "draft_version": session["borrador"]["version"], "usuario": "test", "confirmacion": "CONFIRMAR",
    })
    assert result["ok"] is False
    assert RepositorioBibliotecaRecetas601(tmp_path).listar(incluir_archivadas=True) == []
    menus_path = tmp_path / "DATOS/db/menus.json"
    assert not menus_path.exists() or json.loads(menus_path.read_text(encoding="utf-8")) == []


def test_pending_variant_remains_pending_and_blocks_safe_confirmation(tmp_path: Path):
    session = ImportDocumentService(tmp_path).import_document({"hostai_import_package": _package(
        recipes=[], articles=[], variant_groups=[{
            "name": "Salsa romesco", "versions": [
                {"ingredients": [{"name": "Almendra", "quantity": 1, "unit": "kg"}]},
                {"ingredients": [{"name": "Avellana", "quantity": 1, "unit": "kg"}]},
            ],
        }],
    )})["importacion"]
    assert session["borrador"]["variant_decisions"][0]["decision"] == "PENDIENTE"
    assert any(item["code"] == "VARIANTE_REQUIERE_DECISION" for item in session["borrador"]["validation"]["blocking_errors"])
    assert session["confirmacion_disponible"] is False


def test_pipeline_uses_existing_article_matcher_and_keeps_reference_price_non_applicable(tmp_path: Path):
    stored = RepositorioProductosMaestro601(tmp_path).crear_producto({"nombre": "Naranja", "unidad_base": "kg"})
    response = ImportDocumentService(tmp_path).import_document({"hostai_import_package": _package()})
    session = response["importacion"]
    article = session["borrador"]["catalogo"]["articulos"][0]
    assert response["datos_operativos_modificados"] is False
    assert article["accion"] == "REUTILIZAR"
    assert article["article_id"] == stored["codigo"]
    assert article["precio_compra_importado"] == 1.25
    assert article["precio_referencia_importado"]["currency"] == "EUR"
    assert article["precio_referencia_importado"]["type"] == "PRECIO_REFERENCIA_IMPORTADO"
    assert article["precio_aplicable"] is False
    assert session["documento"]["origen"] == "HOSTAI_IMPORT_PACKAGE"
    assert len(RepositorioProductosMaestro601(tmp_path).listar_productos()) == 1


def test_ambiguous_article_stays_pending_in_canonical_pipeline(tmp_path: Path):
    repository = RepositorioProductosMaestro601(tmp_path)
    repository.crear_producto({"nombre": "Nata cocina 18%", "unidad_base": "l"})
    repository.crear_producto({"nombre": "Nata montar 35%", "unidad_base": "l"})
    response = ImportDocumentService(tmp_path).import_document({"hostai_import_package": _package(
        recipes=[], articles=[{"name": "Nata", "unit": "l"}]
    )})
    article = response["importacion"]["borrador"]["catalogo"]["articulos"][0]
    assert article["accion"] == "REQUIERE_REVISION"
    assert article["article_id"] is None
    assert response["importacion"]["confirmacion_disponible"] is False


def test_supplier_matching_ignores_only_trivial_terminal_punctuation(tmp_path: Path):
    repository = RepositorioProductosMaestro601(tmp_path)
    expected = {
        "CARNES PALAU.": repository.crear_proveedor({"nombre": "CARNES PALAU"})["codigo"],
        "Disbesa.": repository.crear_proveedor({"nombre": "DISBESA"})["codigo"],
        "MAKRO.": repository.crear_proveedor({"nombre": "MAKRO"})["codigo"],
    }
    session = ImportDocumentService(tmp_path).import_document({"hostai_import_package": _package(
        recipes=[], articles=[], suppliers=[{"name": name} for name in (
            "CARNES PALAU.", "Disbesa.", "MAKRO.", "MAKRO.SARDA", "SARDA/DISBESA",
        )],
    )})["importacion"]
    by_name = {item["nombre"]: item for item in session["borrador"]["catalogo"]["proveedores"]}
    for name, provider_id in expected.items():
        assert by_name[name]["accion"] == "REUTILIZAR"
        assert by_name[name]["proveedor_id"] == provider_id
    assert by_name["MAKRO.SARDA"]["accion"] == "REQUIERE_REVISION"
    assert by_name["MAKRO.SARDA"]["proveedor_id"] is None
    assert by_name["SARDA/DISBESA"]["accion"] == "REQUIERE_REVISION"
    assert by_name["SARDA/DISBESA"]["proveedor_id"] is None


@pytest.mark.parametrize("name", ["A.P CROQUETA DE SETAS.", "Plato de bienvenida"])
def test_semantic_non_purchased_type_survives_adapter_and_stays_in_type_review(tmp_path: Path, name: str):
    package = _package(recipes=[], articles=[{
        "name": name, "interpretation": {"classification": "ELABORACION_O_APERITIVO_INTERNO_CANDIDATE"},
    }])
    analysis = PreparedImportPackageAdapter().analyze({"hostai_import_package": package})
    assert analysis["articulos"][0]["tipo_semantico"] == "ELABORACION_O_APERITIVO_INTERNO_CANDIDATE"
    session = ImportDocumentService(tmp_path).import_document({"hostai_import_package": package})["importacion"]
    article = session["borrador"]["catalogo"]["articulos"][0]
    assert article["accion"] == "REQUIERE_REVISION"
    assert article["estado"] == "PENDIENTE"
    assert article["tipo_entidad"] != "ARTICULO_COMPRADO"
    assert session["preview_global"]["contadores"]["articulos_nuevos"] == 0


def test_article_review_exposes_evidence_and_persists_decision_in_memory_draft(tmp_path: Path):
    package = _package(recipes=[], articles=[{
        "name": "A.P CROQUETA DE SETAS.",
        "interpretation": {"classification": "ELABORACION_O_APERITIVO_INTERNO_CANDIDATE", "reason": "prefijo A.P"},
        "provenance": {"sheet": "Listado", "row": 7},
    }])
    service = ImportDocumentService(tmp_path)
    result = service.import_document({"hostai_import_package": package})
    session = result["importacion"]
    article = session["borrador"]["catalogo"]["articulos"][0]
    assert article["nombre"] == "A.P CROQUETA DE SETAS."
    assert article["motivo"]
    assert article["tipo_semantico"] == "ELABORACION_O_APERITIVO_INTERNO_CANDIDATE"
    assert article["origen"]
    assert session["preview_global"]["articulos"]["requiere_revision"][0]["nombre"] == article["nombre"]
    decision = session["borrador"]["article_decisions"][0]
    updated = service.update_draft(session["documento"]["id"], {
        "draft_version": session["borrador"]["draft_version"],
        "recipes": session["borrador"]["recipes"],
        "variant_decisions": session["borrador"].get("variant_decisions", []),
        "article_decisions": [{**decision, "decision": "IGNORAR"}],
    })
    assert updated["ok"] is True
    assert updated["borrador"]["article_decisions"][0]["decision"] == "IGNORAR"
    rehydrated = service.get_import(session["documento"]["id"])["importacion"]
    assert rehydrated["resolucion_identidad"]["articulos"]["requieren_revision"] == 0
    assert rehydrated["preview_global"]["articulos"]["ignorar"][0]["nombre"] == article["nombre"]
    assert updated["datos_reales_modificados"] is False


def test_ignoring_import_record_never_deletes_existing_canonical_candidate(tmp_path: Path):
    repository = RepositorioProductosMaestro601(tmp_path)
    stored = repository.crear_producto({"nombre": "Tabla de quesos", "unidad_base": "ud"})
    before = repository.obtener_producto(stored["codigo"])
    base = _package()
    recipe = {**base["recipes"][0], "name": "Tabla de quesos", "ingredients": []}
    package = _package(recipes=[recipe], articles=[{
        "name": "Tabla de quesos", "unit": "ud",
        "interpretation": {"classification": "PRODUCTO_VENDIBLE_CANDIDATE"},
    }])
    service = ImportDocumentService(tmp_path)
    session = service.import_document({"hostai_import_package": package})["importacion"]
    article = session["borrador"]["catalogo"]["articulos"][0]
    assert article["article_id"] == stored["codigo"]
    decision = session["borrador"]["article_decisions"][0]
    result = service.update_draft(session["documento"]["id"], {
        "draft_version": session["borrador"]["draft_version"],
        "recipes": session["borrador"]["recipes"],
        "variant_decisions": session["borrador"].get("variant_decisions", []),
        "article_decisions": [{**decision, "decision": "IGNORAR"}],
    })
    assert result["ok"] is True
    assert repository.obtener_producto(stored["codigo"]) == before
    current = service.get_import(session["documento"]["id"])["importacion"]
    assert current["preview_global"]["contadores"]["articulos_ignorados"] == 1
    assert current["preview_global"]["contadores"]["articulos_reutilizados"] == 0


def test_article_classified_as_elaboration_exits_pending_and_recipe_counts_unchanged(tmp_path: Path):
    base = _package()
    recipe = {**base["recipes"][0], "name": "Ceviche de corvina", "ingredients": []}
    package = _package(recipes=[recipe], articles=[{
        "name": "Ceviche de corvina",
        "interpretation": {"classification": "RECETA_O_ELABORACION_EXISTENTE_CANDIDATE"},
    }])
    service = ImportDocumentService(tmp_path)
    session = service.import_document({"hostai_import_package": package})["importacion"]
    recipe_count = len(session["borrador"]["recipes"])
    decision = session["borrador"]["article_decisions"][0]
    updated = service.update_draft(session["documento"]["id"], {
        "draft_version": session["borrador"]["draft_version"],
        "recipes": session["borrador"]["recipes"],
        "variant_decisions": session["borrador"].get("variant_decisions", []),
        "article_decisions": [{**decision, "decision": "ES_ELABORACION"}],
    })
    assert updated["ok"] is True
    current = service.get_import(session["documento"]["id"])["importacion"]
    assert current["borrador"]["article_decisions"][0]["decision"] == "ES_ELABORACION"
    assert current["resolucion_identidad"]["articulos"]["requieren_revision"] == 0
    assert current["preview_global"]["articulos"]["es_elaboracion"][0]["nombre"] == "Ceviche de corvina"
    assert current["preview_global"]["articulos"]["crear"] == []
    assert current["preview_global"]["articulos"]["reutilizar"] == []
    assert current["preview_global"]["articulos"]["ignorar"] == []
    assert len(current["borrador"]["recipes"]) == recipe_count
    assert updated["datos_reales_modificados"] is False


def test_thirteen_elaborations_resolve_while_five_ambiguous_purchased_articles_remain(tmp_path: Path):
    repository = RepositorioProductosMaestro601(tmp_path)
    repository.crear_producto({"nombre": "Leche entera A", "unidad_base": "l"})
    repository.crear_producto({"nombre": "Leche entera B", "unidad_base": "l"})
    elaborations = [{
        "name": f"Elaboración Boronat {index}",
        "interpretation": {"classification": "RECETA_O_ELABORACION_EXISTENTE_CANDIDATE"},
    } for index in range(13)]
    purchased = [{"name": "Leche entera", "unit": "l"} for _ in range(5)]
    service = ImportDocumentService(tmp_path)
    session = service.import_document({"hostai_import_package": _package(recipes=[], articles=elaborations + purchased)})["importacion"]
    decisions = session["borrador"]["article_decisions"]
    assert len(decisions) == 18
    classified_ids = {item["id"] for item in session["borrador"]["catalogo"]["articulos"][:13]}
    revised = [{**item, "decision": "ES_ELABORACION"} if item["article_draft_id"] in classified_ids else item for item in decisions]
    result = service.update_draft(session["documento"]["id"], {
        "draft_version": session["borrador"]["draft_version"], "recipes": session["borrador"]["recipes"],
        "variant_decisions": [], "article_decisions": revised,
    })
    assert result["ok"] is True
    current = service.get_import(session["documento"]["id"])["importacion"]
    assert current["resolucion_identidad"]["articulos"]["requieren_revision"] == 5
    assert current["preview_global"]["contadores"]["articulos_reclasificados_elaboracion"] == 13
    assert len(current["preview_global"]["articulos"]["es_elaboracion"]) == 13


def test_ingredient_summary_and_dto_use_post_package_canonical_match(tmp_path: Path):
    stored = RepositorioProductosMaestro601(tmp_path).crear_producto({"nombre": "Naranja", "unidad_base": "kg"})
    session = ImportDocumentService(tmp_path).import_document({"hostai_import_package": _package()})["importacion"]
    ingredient = session["borrador"]["recipes"][0]["ingredients"][0]
    projected = session["documento"]["entidades"][0]["fields"]["ingredientes_estructurados"][0]
    assert ingredient["article_id"] == stored["codigo"]
    assert ingredient["relation_status"] == "COINCIDENCIA_EXACTA_PROPUESTA"
    assert session["resumen"]["ingredientes_detectados"] == 1
    assert session["resumen"]["ingredientes_relacionados"] == 1
    assert projected["articulo_id"] == stored["codigo"]
    assert projected["estado_relacion"] == "relacionado"


def test_semantic_name_variant_still_uses_current_recipe_matcher(tmp_path: Path):
    repository = RepositorioBibliotecaRecetas601(tmp_path)
    repository.crear_ficha_tecnica({
        "nombre": "Salsa naranja", "ingredientes": ["Naranja"], "cantidades": ["1 kg"],
        "elaboracion": "Reducir", "numero_raciones": 1, "tipo": "SALSA",
    })
    stored = repository.listar()[0]
    session = ImportDocumentService(tmp_path).import_document({"hostai_import_package": _package()})["importacion"]
    reused = session["resolucion_identidad"]["recetas"]["grupos"]["ya_canonicas"]
    assert reused and reused[0]["id"]
    assert session["borrador"]["recipes"][0]["duplicate_candidates"][0]["id"] == stored["id"]


def test_boronat_reference_fixture_is_safe_and_separates_context_menu_and_variants():
    fixture = Path(__file__).parent / "fixtures/hostai_import_package_boronat_reference.json"
    analysis = PreparedImportPackageAdapter().analyze({
        "hostai_import_package": json.loads(fixture.read_text(encoding="utf-8"))
    })
    assert len(analysis["recetas"]) == 3
    assert sum(item["posible_variante"] for item in analysis["recetas"]) == 2
    assert [item["tipo"] for item in analysis["menus"]] == ["CONTEXT", "MENU"]
    assert analysis["coste_ia"]["llamadas"] == 0


def test_boronat_corrected_package_analyzes_read_only_and_uses_real_ingredient_matches(tmp_path: Path):
    fixture = Path(__file__).parents[1] / "Documentos/Importaciones/HOSTAI_BORONAT_Codex_Pack (1)/BORONAT_HOSTAI_IMPORT_PACKAGE_0.1.json"
    package = json.loads(fixture.read_text(encoding="utf-8"))
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    session = ImportDocumentService(tmp_path).import_document({"hostai_import_package": package})["importacion"]
    ingredients = [
        ingredient for recipe in session["borrador"]["recipes"]
        for ingredient in recipe["ingredients"]
    ]
    real_related = sum(
        item["relation_status"] in {"RELACIONADO", "COINCIDENCIA_EXACTA_PROPUESTA"}
        and bool(item.get("article_id")) for item in ingredients
    )
    suspicious = [
        item for item in session["borrador"]["catalogo"]["articulos"]
        if "ELABORACION" in str(item.get("tipo_semantico") or "")
    ]
    assert session["resumen"]["ingredientes_detectados"] == 228
    assert all(item.get("name_raw") != "25" for item in ingredients)
    assert session["resumen"]["ingredientes_relacionados"] == real_related
    assert suspicious
    assert all(item["accion"] == "REQUIERE_REVISION" for item in suspicious if not item.get("article_id"))
    assert all(item["tipo_entidad"] != "ARTICULO_COMPRADO" for item in suspicious)
    after = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    assert after == before


def test_analyze_and_preview_do_not_touch_stock_and_confirm_is_idempotence_protected(tmp_path: Path):
    stock = tmp_path / "DATOS/db/stock_lotes.json"
    stock.parent.mkdir(parents=True, exist_ok=True)
    stock.write_text(json.dumps({"fixture": True}), encoding="utf-8")
    before = stock.read_bytes()
    service = ImportDocumentService(tmp_path)
    response = service.import_document({"hostai_import_package": _package()})
    session = response["importacion"]
    assert stock.read_bytes() == before
    result = service.confirm(session["documento"]["id"], {
        "draft_version": 1, "usuario": "test", "confirmacion": "CONFIRMAR",
    })
    assert result["ok"] is True
    assert stock.read_bytes() == before
    recipe = json.loads((tmp_path / "DATOS/db/biblioteca_recetas_601.json").read_text(encoding="utf-8"))["recetas"][0]
    assert recipe["historial_procedencia"][0]["fuente"] == "HOSTAI_IMPORT_PACKAGE"
    article = RepositorioProductosMaestro601(tmp_path).listar_productos()[0]
    assert "HOSTAI_IMPORT_PACKAGE" in article["observaciones"]
    repeated = service.confirm(session["documento"]["id"], {
        "draft_version": 1, "usuario": "test", "confirmacion": "CONFIRMAR",
    })
    assert repeated["ok"] is False
    assert stock.read_bytes() == before


def test_reimport_reuses_recipe_instead_of_duplicating_it(tmp_path: Path):
    first_service = ImportDocumentService(tmp_path)
    first = first_service.import_document({"hostai_import_package": _package()})["importacion"]
    confirmed = first_service.confirm(first["documento"]["id"], {
        "draft_version": 1, "usuario": "test", "confirmacion": "CONFIRMAR",
    })
    assert confirmed["ok"] is True
    second = ImportDocumentService(tmp_path).import_document({"hostai_import_package": _package()})["importacion"]
    assert second["resolucion_identidad"]["recetas"]["ya_canonicas"] == 1
    assert second["resolucion_identidad"]["recetas"]["nuevas_reales"] == 0


def test_real_http_endpoint_accepts_prepared_package_without_operational_write(tmp_path: Path):
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))
    response = client.post("/api/v1/biblioteca/importaciones", json={
        "hostai_import_package": _package()
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["importacion"]["documento"]["origen"] == "HOSTAI_IMPORT_PACKAGE"
    assert payload["datos_reales_modificados"] is False
    assert not (tmp_path / "DATOS/db/stock_lotes.json").exists()


def test_prepare_for_ai_downloads_one_zip_with_original_official_schema_and_neutral_instructions(tmp_path: Path):
    template_source = Path(__file__).parents[1] / "DEVKIT/HOSTAI_IMPORT_PACKAGE_AI_TEMPLATE.md"
    template_target = tmp_path / "DEVKIT/HOSTAI_IMPORT_PACKAGE_AI_TEMPLATE.md"
    template_target.parent.mkdir(parents=True)
    template_target.write_bytes(template_source.read_bytes())
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    original = b"PK\x03\x04XLSX-ORIGINAL-\xc3\xb1"
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))

    response = client.post("/api/v1/biblioteca/importaciones/preparar-para-ia", json={
        "nombre": "Menú verano.xlsx",
        "contenido_base64": base64.b64encode(original).decode("ascii"),
    })

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["x-hostai-domain-writes"] == "0"
    assert "HOSTAI_PARA_IA_Menu_verano.zip" in response.headers["content-disposition"]
    with ZipFile(BytesIO(response.content)) as archive:
        assert archive.namelist() == [
            "documento/Menú verano.xlsx",
            "contrato/HOSTAI_IMPORT_PACKAGE_0.1.schema.json",
            "instrucciones/INSTRUCCIONES_PARA_IA.md",
            "LEEME.txt",
        ]
        assert archive.read("documento/Menú verano.xlsx") == original
        schema = json.loads(archive.read("contrato/HOSTAI_IMPORT_PACKAGE_0.1.schema.json"))
        assert schema == hostai_import_package_json_schema()
        instructions = archive.read("instrucciones/INSTRUCCIONES_PARA_IA.md").decode("utf-8")
        assert "Analiza el documento incluido." in instructions
        assert "schema: hostai.import.package" in instructions
        assert "No inventes identificadores canónicos" in instructions
        assert "ChatGPT" not in instructions
        assert "Claude" not in instructions
        assert "Gemini" not in instructions
        readme = archive.read("LEEME.txt").decode("utf-8")
        assert "Importar resultado de IA" in readme
    after = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    assert after == before
