from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from MODELOS.hostai_import_package import hostai_import_package_json_schema
from SERVICIOS.hostai_chatgpt_import_v01_converter import (
    PROTOTYPE_SCHEMA,
    ChatGPTImportV01Converter,
)
from SERVICIOS.hostai_import_package_adapter import PreparedImportPackageAdapter


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "Documentos/Importaciones/HOSTAI_BORONAT_Codex_Pack (1)"
PROTOTYPE = PACK_DIR / "BORONAT_HOSTAI_IMPORT_CHATGPT.json"


def _prototype() -> dict:
    return json.loads(PROTOTYPE.read_text(encoding="utf-8"))


def _converted() -> dict:
    return ChatGPTImportV01Converter().convert(_prototype())


def test_full_boronat_prototype_converts_and_validates_without_massive_loss():
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


def test_semantics_keep_labels_menus_real_variants_and_suspicious_romesco():
    package = _converted()
    recipe_names = [str(item.get("name") or "").casefold() for item in package["recipes"]]
    variant_names = {str(item.get("name") or "").strip(". ").casefold() for item in package["variant_groups"]}
    assert "tapa" not in recipe_names
    assert all(item["kind"] == "MENU" for item in package["menus"][:12])
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
