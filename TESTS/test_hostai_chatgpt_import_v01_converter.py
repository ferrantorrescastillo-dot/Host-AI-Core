from __future__ import annotations

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from MODELOS.hostai_import_package import hostai_import_package_json_schema
from SERVICIOS.hostai_chatgpt_import_v01_converter import (
    PROTOTYPE_SCHEMA,
    ChatGPTImportV01Converter,
)
from SERVICIOS.hostai_import_package_adapter import PreparedImportPackageAdapter


def _prototype() -> dict:
    def ingredient(name: str, quantity: float = 1) -> dict:
        return {
            "nombre": name, "cantidad_origen": quantity,
            "unidad_columna_origen": "KG", "source_row": 10,
        }

    def recipe(name: str, *, group: str | None = None, quantity: float = 1,
               yield_value: int = 10, row: int = 10) -> dict:
        return {
            "nombre": name, "nombre_normalizado_chatgpt": name.casefold(),
            "rendimiento": yield_value, "unidad_rendimiento_origen": "raciones",
            "coste_total_origen": None, "coste_unitario_origen": None,
            "coste_unitario_label_origen": "Coste ración",
            "ingredientes": [ingredient(f"Ingrediente {name}", quantity)],
            "entity_type_chatgpt": "ELABORACION_INTERNA_CANDIDATE",
            "confidence_extraction": "HIGH", "variant_group_id": group,
            "occurrences": [{"sheet": "Fixture público", "recipe_row": row}],
        }

    recipes = [
        recipe("Agua de jamaica", row=1),
        recipe("Tabla de quesos", group="tabla", yield_value=10, row=2),
        recipe("Tabla de quesos", group="tabla", yield_value=58, row=3),
        recipe("Patatas bravas", group="bravas", quantity=1, row=4),
        recipe("Patatas bravas", group="bravas", quantity=2, row=5),
        recipe("Botifarra con mongetes del ganxet", group="botifarra", quantity=1, row=6),
        recipe("Botifarra con mongetes del ganxet", group="botifarra", quantity=2, row=7),
        recipe("Salsa romesco para calçots", group="romesco", quantity=1, row=8),
        recipe("Salsa romesco para calçots", group="romesco", quantity=2, row=9),
    ]
    return {
        "schema_version": PROTOTYPE_SCHEMA,
        "generator": {"name": "Fixture público", "write_policy": "READ_ONLY_EXTRACTION"},
        "source_document": {"filename": "fixture-publico.xlsx"},
        "interpretation_contract": {"principles": ["PREVIEW -> CONFIRM -> WRITE"]},
        "extraction_summary": {
            "catalog_items_exported": 2, "recipe_structural_versions": 9,
            "recipe_blocks_raw_detected": 9, "menu_blocks_detected": 1,
        },
        "catalog_items": [{
            "codigo_origen": "ART-FLOR", "nombre": "Flor de hibiscus",
            "familia_origen": "Materia prima", "proveedor_origen": "Proveedor fixture",
            "precio_origen": None, "source_row": 1,
            "clasificacion_chatgpt": "ARTICULO_COMPRADO_CANDIDATE",
            "confidence_classification": "HIGH",
        }, {
            "codigo_origen": None, "nombre": "A.P Salsa interna",
            "precio_origen": None, "source_row": 2,
            "clasificacion_chatgpt": "ELABORACION_O_APERITIVO_INTERNO_CANDIDATE",
            "confidence_classification": "MEDIUM",
        }],
        "ignored_source_rows": [], "recipes_and_elaborations": recipes,
        "variant_groups": [],
        "menus_and_containers": [{
            "nombre": "Menú fixture", "source": {"sheet": "Menú"},
            "items": [{"nombre": "Agua de jamaica"}], "confidence_extraction": "HIGH",
        }],
        "supplemental_complex_context": [{
            "sheet": "Contexto fixture", "classification": "COMPLEX_MENU_OR_TEMPLATE_CONTEXT",
            "rows": [{"row": 1, "values": ["TAPA"]}],
        }],
        "hostai_expected_next_stage": {"steps": ["PREVIEW", "CONFIRM", "WRITE"]},
        "semantic_findings": [{
            "type": "REQUIERE_REVISION", "source_token": "Salsa romesco",
            "finding": "Título copiado que requiere revisar su variante.", "confidence": "MEDIUM",
        }],
    }


def _converted() -> dict:
    return ChatGPTImportV01Converter().convert(_prototype())


def test_representative_public_prototype_converts_and_validates_without_loss():
    source = _prototype()
    package = _converted()
    validated = PreparedImportPackageAdapter.validate(package)
    summary = source["extraction_summary"]
    versions = len(package["recipes"]) + sum(len(group["versions"]) for group in package["variant_groups"])
    occurrences = sum(len(item.get("occurrences") or []) for item in package["recipes"])
    occurrences += sum(len(version.get("occurrences") or []) for group in package["variant_groups"] for version in group["versions"])
    assert validated.schema == "hostai.import.package"
    assert validated.version == "0.1"
    assert len(package["articles"]) == summary["catalog_items_exported"]
    assert versions == summary["recipe_structural_versions"] - 1  # una pareja escalada se vuelve una receta lógica
    assert occurrences == summary["recipe_blocks_raw_detected"]
    assert len([item for item in package["menus"] if item["kind"] == "MENU"]) == summary["menu_blocks_detected"]
    assert package["metadata"]["migration_warnings"] == []


def test_semantics_keep_labels_menus_variants_and_suspicious_romesco():
    package = _converted()
    recipe_names = [str(item.get("name") or "").casefold() for item in package["recipes"]]
    variant_names = {str(item.get("name") or "").strip(". ").casefold() for item in package["variant_groups"]}
    assert "tapa" not in recipe_names
    assert package["menus"][0]["kind"] == "MENU"
    assert any(item["kind"] == "CONTEXT" for item in package["menus"])
    assert "patatas bravas" in variant_names
    assert "botifarra con mongetes del ganxet" in variant_names
    assert "salsa romesco para calçots" in variant_names
    assert any("título copiado" in str(item.get("reason") or "").casefold()
               or "romesco" in str(item.get("name") or "").casefold()
               for item in package["ambiguities"])
    scaled = next(item for item in package["recipes"] if str(item.get("name")).casefold() == "tabla de quesos")
    assert scaled["yield"] is None
    assert len(scaled["occurrences"]) == 2
    assert {item["value"] for item in scaled["observed"]["yield_versions"]} == {10, 58}


def test_converter_reports_unknown_top_level_fields_instead_of_inventing_mapping():
    source = _prototype()
    source["future_unmapped_block"] = {"anything": True}
    package = ChatGPTImportV01Converter().convert(source)
    assert package["metadata"]["migration_warnings"] == [{
        "type": "CAMPO_NO_MIGRADO", "path": "$.future_unmapped_block",
        "reason": "Campo superior desconocido.",
    }]


def test_full_converted_package_passes_real_http_endpoint_analyze_only(tmp_path: Path):
    stock = tmp_path / "DATOS/db/stock_lotes.json"
    stock.parent.mkdir(parents=True, exist_ok=True)
    stock.write_text('{"fixture":true}', encoding="utf-8")
    before = stock.read_bytes()
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))
    response = client.post("/api/v1/biblioteca/importaciones", json={
        "hostai_import_package": _converted(),
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["datos_reales_modificados"] is False
    assert payload["importacion"]["documento"]["origen"] == "HOSTAI_IMPORT_PACKAGE"
    assert stock.read_bytes() == before


def test_old_prototype_schema_is_rejected_by_real_endpoint_with_human_error(tmp_path: Path):
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))
    response = client.post("/api/v1/biblioteca/importaciones", json={
        "hostai_import_package": _prototype(),
    })
    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["code"] == "hostai_import_package_invalido"
    assert "Schema HostAIImportPackage no reconocido" in payload["error"]["message"]


def test_exportable_schema_comes_from_real_contract_constants():
    schema = hostai_import_package_json_schema()
    assert schema["properties"]["schema"]["const"] == "hostai.import.package"
    assert schema["properties"]["version"]["const"] == "0.1"
    assert schema["x-hostai-security"]["proposal_only"] is True
    assert PROTOTYPE_SCHEMA != schema["properties"]["schema"]["const"]
