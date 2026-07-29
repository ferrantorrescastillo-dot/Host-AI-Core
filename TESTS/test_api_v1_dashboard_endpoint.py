from __future__ import annotations

import json
from pathlib import Path

from API.app import HostAIPlatformAPI
from API.contracts.http_models import ApiRequest


def test_get_api_v1_dashboard_devuelve_http_200_y_json_valido(tmp_path: Path) -> None:
    api = HostAIPlatformAPI(base_dir=tmp_path)

    response = api.handle(ApiRequest(method="GET", path="/api/v1/dashboard"))

    assert response.status_code == 200
    payload = response.payload
    assert payload.get("ok") is True
    assert payload.get("version") == "1.0"
    assert payload.get("modo_seguro") is True
    assert payload.get("datos_reales_modificados") is False
    dashboard = payload.get("dashboard") or {}
    assert isinstance(dashboard, dict)
    for key in [
        "estado_general",
        "prioridad",
        "pendientes",
        "riesgos",
        "recomendaciones",
        "evento_activo",
        "workflows",
    ]:
        assert key in dashboard
    json.dumps(payload)


def test_get_api_v1_dashboard_reutiliza_flujo_executive(monkeypatch, tmp_path: Path) -> None:
    from API.facade.core_public_api02 import CorePublicApi02Facade

    called = {"executive": 0}

    def fake_executive(self, query):
        called["executive"] += 1
        return {
            "ok": True,
            "version": "1.0",
            "modo_seguro": True,
            "datos_reales_modificados": False,
            "executive": {
                "ok": True,
                "estado_general": "estable",
                "prioridad_inmediata": {"workflow": "GOBERNANZA", "titulo": "Seguimiento"},
                "pendientes": [{"codigo": "X"}],
                "riesgos": [],
                "recomendaciones": [],
                "evento": {"id": "EVT-1", "nombre": "Evento test"},
                "workflows_priorizados": [{"workflow": "GOBERNANZA"}],
                "datos_reales_modificados": False,
            },
        }

    monkeypatch.setattr(CorePublicApi02Facade, "executive", fake_executive)

    api = HostAIPlatformAPI(base_dir=tmp_path)
    response = api.handle(ApiRequest(method="GET", path="/api/v1/dashboard"))

    assert response.status_code == 200
    assert called["executive"] == 1
    payload = response.payload
    assert payload.get("ok") is True
    assert payload.get("datos_reales_modificados") is False
    assert payload.get("dashboard", {}).get("estado_general") == "estable"
    assert payload.get("dashboard", {}).get("evento_activo", {}).get("id") == "EVT-1"


def test_get_api_v1_dashboard_error_homogeneo_sin_traceback(monkeypatch, tmp_path: Path) -> None:
    from API.facade.core_public_api02 import CorePublicApi02Facade

    def failing_executive(self, query):
        raise RuntimeError("Fallo interno C:\\secreto\\ruta")

    monkeypatch.setattr(CorePublicApi02Facade, "executive", failing_executive)

    api = HostAIPlatformAPI(base_dir=tmp_path)
    response = api.handle(ApiRequest(method="GET", path="/api/v1/dashboard"))

    assert response.status_code == 200
    payload = response.payload
    assert payload.get("ok") is False
    assert payload.get("version") == "1.0"
    assert payload.get("modo_seguro") is True
    assert payload.get("datos_reales_modificados") is False
    assert payload.get("error", {}).get("code") == "dashboard_unavailable"
    serialized = json.dumps(payload)
    assert "Traceback" not in serialized
    assert "C:\\\\" not in serialized
