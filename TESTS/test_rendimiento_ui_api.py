from __future__ import annotations

import json
from pathlib import Path

from API.app import HostAIPlatformAPI
from API.contracts.http_models import ApiRequest
from API.http_server import create_app
from CORE.entidades.escandallo import Escandallo
from CORE.entidades.ingrediente import Ingrediente
from CORE.entidades.receta import EstadoRendimiento, OrigenRendimiento, Receta
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos
from fastapi.testclient import TestClient


def _fixture(base: Path) -> Path:
    db = base / "DATOS" / "db"
    db.mkdir(parents=True)
    path = db / "escandallos_canonicos.json"
    RepositorioEscandallos(path).guardar_todos([Escandallo(Receta(
        "REC-CREMA", "Crema", 7, "u",
        [Ingrediente("ART-1", "Leche", 1, "kg", articulo_id="ART-1")],
        estado_rendimiento=EstadoRendimiento.IMPORTADO,
        origen_rendimiento=OrigenRendimiento("FIXTURE", "test"),
    ), 10)])
    (db / "articulos.json").write_text(json.dumps([
        {"codigo": "ART-1", "nombre": "Leche", "precio": 2, "unidad": "kg"},
    ]), encoding="utf-8")
    return path


def _authorize(monkeypatch) -> None:
    monkeypatch.setenv("HOST_AI_INTERNAL_USER_ID", "USR-CHEF")
    monkeypatch.setenv("HOST_AI_INTERNAL_TENANT_ID", "TENANT-1")
    monkeypatch.setenv("HOST_AI_INTERNAL_ROLES", "chef")
    monkeypatch.setenv("HOST_AI_INTERNAL_SCOPES", "escandallos:write")


def test_api_interna_preview_por_unidad_confirma_y_actualiza_read(tmp_path: Path, monkeypatch) -> None:
    path = _fixture(tmp_path)
    _authorize(monkeypatch)
    api = HostAIPlatformAPI(base_dir=tmp_path)
    body = {"cantidad": 0.18, "unidad": "kg", "modo": "POR_UNIDAD"}

    preview = api.handle(ApiRequest(
        method="POST", path="/api/v1/biblioteca/elaboraciones/REC-CREMA/rendimiento/preview",
        request_id="REQ-PREVIEW", body=body,
    ))
    assert preview.status_code == 200
    assert preview.payload["rendimiento_neto_propuesto"]["cantidad"] == 1.26
    assert preview.payload["incidencias"] == []
    assert preview.payload["datos_reales_modificados"] is False

    confirmed = api.handle(ApiRequest(
        method="POST", path="/api/v1/biblioteca/elaboraciones/REC-CREMA/rendimiento/confirmar",
        request_id="REQ-CONFIRM", body={**body, "preview_token": preview.payload["preview_token"]},
    ))
    assert confirmed.status_code == 200
    assert confirmed.payload["rendimiento_neto"]["cantidad"] == 1.26
    assert confirmed.payload["rendimiento_neto"]["origen"]["actor_id"] == "USR-CHEF"
    assert confirmed.payload["datos_reales_modificados"] is True

    detail = api.handle(ApiRequest(
        method="GET", path="/api/v1/biblioteca/elaboraciones/REC-CREMA",
        request_id="REQ-READ",
    ))
    assert detail.payload["permisos"]["confirmar_rendimiento"] is True
    assert detail.payload["elaboracion"]["receta"]["rendimiento"] == 7
    assert detail.payload["elaboracion"]["receta"]["unidad_rendimiento"] == "u"
    assert detail.payload["elaboracion"]["receta"]["rendimiento_neto"]["cantidad"] == 1.26
    assert RepositorioEscandallos(path).listar()[0].coste_total == 10


def test_api_sin_scope_mantiene_read_y_deniega_preview(tmp_path: Path, monkeypatch) -> None:
    path = _fixture(tmp_path)
    before = path.read_bytes()
    monkeypatch.setenv("HOST_AI_INTERNAL_USER_ID", "USR-SIN-SCOPE")
    monkeypatch.setenv("HOST_AI_INTERNAL_TENANT_ID", "TENANT-1")
    monkeypatch.delenv("HOST_AI_INTERNAL_SCOPES", raising=False)
    api = HostAIPlatformAPI(base_dir=tmp_path)

    detail = api.handle(ApiRequest(
        method="GET", path="/api/v1/biblioteca/elaboraciones/REC-CREMA", request_id="REQ-READ",
    ))
    assert detail.status_code == 200
    assert detail.payload["permisos"]["confirmar_rendimiento"] is False

    denied = api.handle(ApiRequest(
        method="POST", path="/api/v1/biblioteca/elaboraciones/REC-CREMA/rendimiento/preview",
        request_id="REQ-DENIED", body={"cantidad": 1.26, "unidad": "kg"},
    ))
    assert denied.status_code == 403
    assert denied.payload["error"]["code"] == "unauthorized"
    assert path.read_bytes() == before


def test_api_rechaza_estimacion_parcial_sin_aceptacion_explicita(tmp_path: Path, monkeypatch) -> None:
    path = _fixture(tmp_path)
    before = path.read_bytes()
    _authorize(monkeypatch)
    api = HostAIPlatformAPI(base_dir=tmp_path)
    body = {"cantidad": 1.276, "unidad": "kg", "modo": "TOTAL", "propuesta_origen": "TEORICO_PARCIAL"}
    preview = api.handle(ApiRequest(
        method="POST", path="/api/v1/biblioteca/elaboraciones/REC-CREMA/rendimiento/preview",
        request_id="REQ-PARTIAL-PREVIEW", body=body,
    ))
    assert preview.status_code == 200
    assert preview.payload["propuesta_origen"] == "TEORICO_PARCIAL"
    assert path.read_bytes() == before

    rejected = api.handle(ApiRequest(
        method="POST", path="/api/v1/biblioteca/elaboraciones/REC-CREMA/rendimiento/confirmar",
        request_id="REQ-PARTIAL-REJECT", body={**body, "preview_token": preview.payload["preview_token"]},
    ))
    assert rejected.status_code == 422
    assert rejected.payload["error"]["code"] == "partial_estimate_acceptance_required"
    assert path.read_bytes() == before

    accepted = api.handle(ApiRequest(
        method="POST", path="/api/v1/biblioteca/elaboraciones/REC-CREMA/rendimiento/confirmar",
        request_id="REQ-PARTIAL-ACCEPT", body={
            **body, "preview_token": preview.payload["preview_token"], "acepta_estimacion_parcial": True,
        },
    ))
    assert accepted.status_code == 200
    assert accepted.payload["rendimiento_neto"]["cantidad"] == 1.276


def test_api_rechaza_preview_obsoleto_sin_sobrescribir(tmp_path: Path, monkeypatch) -> None:
    path = _fixture(tmp_path)
    _authorize(monkeypatch)
    api = HostAIPlatformAPI(base_dir=tmp_path)
    body = {"cantidad": 1.26, "unidad": "kg", "modo": "TOTAL"}
    preview = api.handle(ApiRequest(
        method="POST", path="/api/v1/biblioteca/elaboraciones/REC-CREMA/rendimiento/preview",
        request_id="REQ-1", body=body,
    ))
    stored = json.loads(path.read_text(encoding="utf-8"))
    stored["escandallos"][0]["receta"]["nombre"] = "Cambio concurrente"
    path.write_text(json.dumps(stored, ensure_ascii=False), encoding="utf-8")
    before_confirm = path.read_bytes()

    result = api.handle(ApiRequest(
        method="POST", path="/api/v1/biblioteca/elaboraciones/REC-CREMA/rendimiento/confirmar",
        request_id="REQ-2", body={**body, "preview_token": preview.payload["preview_token"]},
    ))
    assert result.status_code == 409
    assert result.payload["error"]["code"] == "stale_or_invalid_preview"
    assert path.read_bytes() == before_confirm


def test_http_real_parsea_018_por_unidad_y_preview_no_persiste(tmp_path: Path, monkeypatch) -> None:
    path = _fixture(tmp_path)
    before = path.read_bytes()
    _authorize(monkeypatch)
    client = TestClient(create_app(HostAIPlatformAPI(base_dir=tmp_path)))

    response = client.post(
        "/api/v1/biblioteca/elaboraciones/REC-CREMA/rendimiento/preview",
        json={"cantidad": 0.18, "unidad": "kg", "modo": "POR_UNIDAD"},
        headers={"Origin": "http://localhost:5174"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["rendimiento_neto_propuesto"]["cantidad"] == 1.26
    assert payload["rendimiento_neto_propuesto"]["unidad"] == "kg"
    assert payload["modo_entrada"] == "POR_UNIDAD"
    assert payload["datos_reales_modificados"] is False
    assert path.read_bytes() == before
