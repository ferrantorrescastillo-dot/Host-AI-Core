from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from SERVICIOS.confirmacion_importacion_biblioteca import (
    ImportConfirmationService,
    ImportSessionRepository,
)
from SERVICIOS.borrador_importacion_biblioteca import ImportDraftService


def _session() -> dict:
    return {
        "documento": {"id": "IMP-1", "nombre": "receta.docx"},
        "estado": "PENDIENTE_REVISION",
        "borrador": {
            "version": 2,
            "recipes": [{
                "id": "R-1", "title": "Crema de calabaza", "entity_type": "PRINCIPAL",
                "parent_recipe_id": None, "proposed_action": "CREAR_RECETA",
                "description": "", "procedure": ["Cocer y triturar."], "servings": 4,
                "yield_value": 4, "notes": "Revisada", "duplicate_candidates": [],
                "ingredients": [{
                    "id": "I-1", "name_raw": "Calabaza", "quantity_raw": "1",
                    "quantity": 1.0, "unit": "kg", "unit_raw": "kg",
                    "relation_status": "SIN_RELACIONAR", "article_id": None,
                    "observations": "",
                }],
            }],
        },
        "historial": [],
    }


def test_confirmacion_persiste_receta_estado_e_historial_y_sobrevive_reinicio(tmp_path: Path) -> None:
    repository = ImportSessionRepository(tmp_path)
    sessions = {"IMP-1": _session()}
    repository.save_all(sessions)
    result = ImportConfirmationService(tmp_path, repository).confirm(
        sessions, "IMP-1",
        {"draft_version": 2, "usuario": "chef", "confirmacion": "CONFIRMAR"},
    )
    assert result["ok"] is True
    assert sessions["IMP-1"]["estado"] == "CONFIRMADA"
    assert sessions["IMP-1"]["historial"][0]["usuario"] == "chef"
    assert ImportSessionRepository(tmp_path).load_all()["IMP-1"]["estado"] == "CONFIRMADA"
    persisted_imports = json.loads(
        (tmp_path / "DATOS/db/biblioteca_importaciones_web.json").read_text(encoding="utf-8")
    )
    assert persisted_imports["schema_version"] == 2
    assert persisted_imports["created_at"] and persisted_imports["updated_at"]
    recipes = json.loads(
        (tmp_path / "DATOS/db/biblioteca_recetas_601.json").read_text(encoding="utf-8")
    )["recetas"]
    assert recipes[0]["nombre"] == "Crema de calabaza"
    assert not (tmp_path / "DATOS/db/articulos.json").exists()
    assert not (tmp_path / "DATOS/db/biblioteca_escandallos_601.json").exists()
    assert not (tmp_path / "DATOS/db/proveedores.json").exists()
    assert not (tmp_path / "DATOS/db/compras_producto_proveedor.json").exists()
    assert not (tmp_path / "DATOS/facturas/historico_precios.json").exists()


def test_confirmacion_bloquea_version_antigua_y_datos_incompletos_sin_escribir_dominio(
    tmp_path: Path,
) -> None:
    repository = ImportSessionRepository(tmp_path)
    sessions = {"IMP-1": _session()}
    sessions["IMP-1"]["borrador"]["recipes"][0]["title"] = ""
    result = ImportConfirmationService(tmp_path, repository).confirm(
        sessions, "IMP-1",
        {"draft_version": 1, "usuario": "chef", "confirmacion": "CONFIRMAR"},
    )
    assert result["ok"] is False
    assert {item["validacion"] for item in result["resultado"]["errores"]} >= {
        "VERSION_CONFLICT", "TITULO_VACIO",
    }
    title_error = next(
        item for item in result["resultado"]["errores"]
        if item["code"] == "TITULO_VACIO"
    )
    assert title_error == {
        "code": "TITULO_VACIO",
        "level": "BLOQUEANTE",
        "recipe_id": "R-1",
        "recipe_title": "Sin título",
        "recipe_index": 0,
        "ingredient_id": None,
        "ingredient_index": None,
        "field": "title",
        "message": "La sección necesita un título.",
        "entidad": "R-1",
        "validacion": "TITULO_VACIO",
        "accion": "confirmar",
        "mensaje": "La sección necesita un título.",
    }
    assert not (tmp_path / "DATOS/db/biblioteca_recetas_601.json").exists()


def test_confirmacion_exige_aceptacion_explicita(tmp_path: Path) -> None:
    repository = ImportSessionRepository(tmp_path)
    sessions = {"IMP-1": _session()}
    result = ImportConfirmationService(tmp_path, repository).confirm(
        sessions, "IMP-1", {"draft_version": 2, "usuario": "chef"}
    )
    assert result["error"]["code"] == "confirmation_required"
    assert not (tmp_path / "DATOS/db/biblioteca_recetas_601.json").exists()


def test_http_confirmacion_estado_e_historial(tmp_path: Path) -> None:
    api = HostAIPlatformAPI(base_dir=tmp_path)
    service = api.facade._get_biblioteca_import_service()
    service._sessions["IMP-1"] = _session()
    service.repository.save_all(service._sessions)
    client = TestClient(create_app(api))

    confirmed = client.post(
        "/api/v1/biblioteca/importaciones/IMP-1/confirmar",
        json={"draft_version": 2, "usuario": "chef", "confirmacion": "CONFIRMAR"},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["resultado"]["estado"] == "COMPLETADA"
    assert client.get("/api/v1/biblioteca/importaciones/IMP-1/estado").json()["estado"] == "CONFIRMADA"
    history = client.get("/api/v1/biblioteca/importaciones/IMP-1/historial").json()
    assert history["total"] == 1
    assert history["historial"][0]["usuario"] == "chef"


def test_confirmacion_usa_ingredientes_anadidos_al_borrador_revisado(tmp_path: Path) -> None:
    drafts = ImportDraftService(tmp_path)
    draft = drafts.build(
        import_id="IMP-EDIT",
        classification="RECETA",
        confidence=0.8,
        recipes=[{
            "id_origen": "REC-NARANJA",
            "nombre": "Salsa de naranja",
            "ingredientes_estructurados": [],
            "pasos": ["Reducir y triturar."],
            "numero_raciones": 4,
        }],
    )
    revised = drafts.update(draft, {
        "draft_version": 1,
        "recipes": [{
            **draft["recipes"][0],
            "servings": 4,
            "ingredients": [{
                "id": "NEW-NARANJA",
                "quantity_raw": "2",
                "unit_raw": "kg",
                "name_raw": "Naranja",
                "observations": "Sin piel",
                "relation_status": "SIN_RELACIONAR",
                "article_id": None,
            }],
        }],
    })
    sessions = {"IMP-EDIT": {
        "documento": {"id": "IMP-EDIT", "nombre": "salsa.docx"},
        "estado": "PENDIENTE_REVISION",
        "borrador": revised,
        "historial": [],
    }}
    repository = ImportSessionRepository(tmp_path)
    repository.save_all(sessions)

    result = ImportConfirmationService(tmp_path, repository).confirm(
        sessions, "IMP-EDIT",
        {"draft_version": 2, "usuario": "chef", "confirmacion": "CONFIRMAR"},
    )

    assert result["ok"] is True
    recipes = json.loads(
        (tmp_path / "DATOS/db/biblioteca_recetas_601.json").read_text(encoding="utf-8")
    )["recetas"]
    assert recipes[0]["ingredientes"] == ["Naranja"]
    assert recipes[0]["cantidades"] == ["2 kg"]
