from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.contracts.http_models import ApiResponse
from API.http_server import create_app


def _make_client(tmp_path: Path) -> TestClient:
    app = create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path))
    return TestClient(app)


def test_http_health(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload.get("ok") is True
    assert isinstance(payload.get("health"), dict)
    assert payload.get("datos_reales_modificados") is False


def test_http_version(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    response = client.get("/api/v1/version")

    assert response.status_code == 200
    payload = response.json()
    assert payload.get("ok") is True
    assert isinstance(payload.get("version_info"), dict)
    assert payload.get("datos_reales_modificados") is False


def test_http_executive(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    response = client.get("/api/v1/executive")

    assert response.status_code == 200
    payload = response.json()
    assert payload.get("ok") is True
    assert isinstance(payload.get("executive"), dict)
    assert payload.get("datos_reales_modificados") is False


def test_http_dashboard(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload.get("ok") is True
    assert isinstance(payload.get("dashboard"), dict)
    assert payload.get("datos_reales_modificados") is False


def test_http_dashboard_expone_contrato_compras(tmp_path: Path) -> None:
    db_dir = tmp_path / "DATOS" / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    (db_dir / "compras_proveedores.json").write_text(
        json.dumps([{"id": "PROV-HTTP", "nombre": "Proveedor HTTP", "estado": "activo"}]),
        encoding="utf-8",
    )

    response = _make_client(tmp_path).get("/api/v1/dashboard")

    assert response.status_code == 200
    compras = response.json()["dashboard"]["modulos"]["compras"]
    assert compras["estado"] == "datos_disponibles"
    assert compras["necesidades_pendientes"] == 0
    assert compras["propuestas_pendientes"] == 0
    assert compras["total_proveedores"] == 1
    assert compras["proveedores"][0]["id"] == "PROV-HTTP"
    assert compras["propuestas"] == []
    assert compras["historial"] == []


def test_http_dashboard_expone_contrato_eventos(tmp_path: Path) -> None:
    db_dir = tmp_path / "DATOS" / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    (db_dir / "eventos.json").write_text(
        json.dumps(
            [
                {
                    "id": "EVT-HTTP",
                    "nombre": "Evento HTTP",
                    "fecha": "2099-09-10",
                    "pax": 45,
                    "estado": "pendiente",
                    "servicios": [],
                }
            ]
        ),
        encoding="utf-8",
    )

    response = _make_client(tmp_path).get("/api/v1/dashboard")

    assert response.status_code == 200
    eventos = response.json()["dashboard"]["modulos"]["eventos"]
    assert eventos["total"] == 1
    assert eventos["resumen"]["pax_total"] == 45
    assert eventos["items"][0]["id"] == "EVT-HTTP"
    assert eventos["items"][0]["avisos"] == ["Faltan servicios."]


def test_http_chat(monkeypatch, tmp_path: Path) -> None:
    from API.facade.core_public_api02 import CorePublicApi02Facade

    class FakeChatService:
        def enviar(self, texto: str, contexto=None):
            return {
                "ok": True,
                "tipo_mensaje": "RESULTADO",
                "mensaje": f"eco: {texto}",
                "rol": "host_ai",
                "timestamp": "2026-07-29T12:00:00",
                "datos": {"contexto": dict(contexto or {})},
            }

        def estado_sesion(self):
            return {"contexto_activo": "HOME"}

    monkeypatch.setattr(CorePublicApi02Facade, "_build_chat_service", lambda self: FakeChatService())

    client = _make_client(tmp_path)
    response = client.post("/api/v1/chat", json={"mensaje": "hola", "contexto": {"k": "v"}})

    assert response.status_code == 200
    payload = response.json()
    assert payload.get("ok") is True
    assert payload.get("respuesta") == "eco: hola"
    assert isinstance(payload.get("chat"), dict)
    assert payload.get("datos_reales_modificados") is False


def test_http_request_id_preservado(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    response = client.get("/api/v1/health", headers={"X-Request-ID": "REQ-HTTP-001"})

    assert response.status_code == 200
    payload = response.json()
    assert payload.get("request_id") == "REQ-HTTP-001"


def test_http_404_homogeneo(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    response = client.get("/api/v1/no-existe")

    assert response.status_code == 404
    payload = response.json()
    assert payload.get("ok") is False
    assert payload.get("error", {}).get("status") == 404
    assert payload.get("error", {}).get("code") == "not_found"
    assert payload.get("datos_reales_modificados") is False


def test_http_error_interno_sin_traceback(tmp_path: Path) -> None:
    class FailingPlatform:
        def handle(self, request):
            raise RuntimeError("Fallo interno C:\\ruta\\secreta")

    app = create_app(platform_api=FailingPlatform())
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 500
    payload = response.json()
    assert payload.get("ok") is False
    assert payload.get("error", {}).get("code") == "internal_error"
    serialized = json.dumps(payload)
    assert "Traceback" not in serialized
    assert "C:\\\\" not in serialized


def test_http_cors_host_ai_web_en_articulos_y_dashboard(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    origins = (
        "http://localhost:5173",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
    )
    endpoints = ("/api/v1/articulos", "/api/v1/dashboard")

    for origin in origins:
        for endpoint in endpoints:
            preflight = client.options(
                endpoint,
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "GET",
                },
            )
            assert preflight.status_code in (200, 204)
            assert preflight.headers.get("access-control-allow-origin") == origin

            response = client.get(endpoint, headers={"Origin": origin})
            assert response.status_code == 200
            assert response.headers.get("access-control-allow-origin") == origin


def test_http_datos_reales_modificados_false_en_endpoints_versionados(monkeypatch, tmp_path: Path) -> None:
    from API.facade.core_public_api02 import CorePublicApi02Facade

    class FakeChatService:
        def enviar(self, texto: str, contexto=None):
            return {
                "ok": True,
                "tipo_mensaje": "RESULTADO",
                "mensaje": f"eco: {texto}",
            }

        def estado_sesion(self):
            return {"contexto_activo": "HOME"}

    monkeypatch.setattr(CorePublicApi02Facade, "_build_chat_service", lambda self: FakeChatService())

    client = _make_client(tmp_path)
    responses = [
        client.get("/api/v1/health"),
        client.get("/api/v1/version"),
        client.get("/api/v1/executive"),
        client.get("/api/v1/dashboard"),
        client.post("/api/v1/chat", json={"mensaje": "hola", "contexto": {}}),
    ]

    for response in responses:
        assert response.status_code == 200
        assert response.json().get("datos_reales_modificados") is False
