from __future__ import annotations

import base64
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app


ROOT = Path(__file__).resolve().parents[1]
EXCEL = ROOT / "Documentos/Escandallos Boronat.xlsx"
PACKAGE = ROOT / "Documentos/Importaciones/HOSTAI_BORONAT_Codex_Pack (1)/BORONAT_HOSTAI_IMPORT_PACKAGE_0.1.json"


def _hashes(path: Path) -> dict[str, str]:
    return {
        str(item.relative_to(path)): hashlib.sha256(item.read_bytes()).hexdigest()
        for item in path.rglob("*") if item.is_file()
    }


def _changed(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))


def _clone() -> tuple[tempfile.TemporaryDirectory[str], Path, dict[str, str]]:
    holder = tempfile.TemporaryDirectory(prefix="hostai-boronat-ab-")
    base = Path(holder.name)
    source = ROOT / "DATOS/db"
    shutil.copytree(source, base / "DATOS/db")
    return holder, base, _hashes(base / "DATOS/db")


def _post(base: Path, body: dict[str, Any]) -> dict[str, Any]:
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=base)))
    response = client.post("/api/v1/biblioteca/importaciones", json=body)
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text[:1000]}")
    return response.json()["importacion"]


def _metrics(session: dict[str, Any]) -> dict[str, Any]:
    identity = session.get("resolucion_identidad") or {}
    recipes = identity.get("recetas") or {}
    articles = identity.get("articulos") or {}
    variants = identity.get("variantes") or {}
    analysis = session.get("analisis_restaurante") or {}
    entities = session.get("documento", {}).get("entidades") or []
    recipe_names = [str(item.get("name") or "") for item in entities if item.get("kind") == "RECETA"]
    false_names = [name for name in recipe_names if name.strip().casefold() == "tapa" or name.strip().casefold().startswith("menu ")]
    preview = session.get("preview_global", {}).get("contadores") or {}
    providers = session.get("preview_global", {}).get("proveedores") or {}
    return {
        "recipes": {
            "total": recipes.get("total", 0), "canonical": recipes.get("ya_canonicas", 0),
            "legacy": recipes.get("ya_conocidas_legacy", 0), "new": recipes.get("nuevas_reales", 0),
            "variants": recipes.get("posibles_variantes", 0), "ambiguous": recipes.get("requieren_revision", 0),
        },
        "articles": {
            "total": articles.get("total", 0), "reused": articles.get("ya_existentes", 0),
            "new": articles.get("nuevos_reales", 0), "ambiguous": articles.get("requieren_revision", 0),
        },
        "providers": {
            "new": preview.get("proveedores_nuevos", 0), "reused": preview.get("proveedores_reutilizados", 0),
            "review": len(providers.get("requiere_revision") or []),
        },
        "menus": sum(item.get("kind") == "MENU" and item.get("fields", {}).get("tipo") != "CONTEXT" for item in entities),
        "contexts": sum(item.get("kind") == "MENU" and item.get("fields", {}).get("tipo") == "CONTEXT" for item in entities),
        "variant_occurrences": variants.get("apariciones", 0),
        "variant_groups": variants.get("grupos", 0),
        "exact_duplicates_collapsed": int(
            analysis.get("package_metadata", {}).get("extraction_summary", {}).get("exact_duplicate_occurrences_collapsed")
            or variants.get("duplicados_exactos_colapsados", 0)
        ),
        "ambiguities": len(analysis.get("decisiones_usuario") or []),
        "human_decisions": int(analysis.get("resumen", {}).get("decisiones_usuario") or 0),
        "technical_warnings": len(analysis.get("warnings_tecnicos") or []),
        "false_recipe_names": false_names,
        "confirmation_available": session.get("confirmacion_disponible"),
    }


def main() -> int:
    excel_holder, excel_base, excel_before = _clone()
    package_holder, package_base, package_before = _clone()
    try:
        excel_session = _post(excel_base, {"archivos": [{
            "nombre": EXCEL.name, "tipo_mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "contenido_base64": base64.b64encode(EXCEL.read_bytes()).decode("ascii"),
        }]})
        package_session = _post(package_base, {
            "hostai_import_package": json.loads(PACKAGE.read_text(encoding="utf-8")),
        })
        excel_after = _hashes(excel_base / "DATOS/db")
        package_after = _hashes(package_base / "DATOS/db")
        excel_changed = _changed(excel_before, excel_after)
        package_changed = _changed(package_before, package_after)
        session_files = {"biblioteca_importaciones_web.json"}
        result = {
            "excel": _metrics(excel_session), "package": _metrics(package_session),
            "writes": {
                "excel_changed_files": excel_changed,
                "package_changed_files": package_changed,
                "excel_operational_domain_unchanged": not (set(excel_changed) - session_files),
                "package_operational_domain_unchanged": not (set(package_changed) - session_files),
                "analyze_session_persisted": bool(set(excel_changed + package_changed) & session_files),
            },
            "analyze_only": True,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        excel_holder.cleanup()
        package_holder.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
