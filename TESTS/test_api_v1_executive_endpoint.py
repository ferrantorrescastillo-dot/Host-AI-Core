from __future__ import annotations

import json
from pathlib import Path

from API.app import HostAIPlatformAPI
from API.contracts.http_models import ApiRequest


def test_get_api_v1_executive_devuelve_http_200_y_json_valido(tmp_path: Path) -> None:
    api = HostAIPlatformAPI(base_dir=tmp_path)
    request = ApiRequest(method="GET", path="/api/v1/executive")

    response = api.handle(request)

    assert response.status_code == 200
    payload = response.payload
    assert payload.get("ok") is True
    assert payload.get("version") == "1.0"
    assert payload.get("modo_seguro") is True
    assert payload.get("datos_reales_modificados") is False
    assert isinstance(payload.get("executive"), dict)
    json.dumps(payload)


def test_get_api_v1_executive_reutiliza_host_ai_executive(monkeypatch, tmp_path: Path) -> None:
    from API.facade import core_public_api02 as module

    called = {"analizar_restaurante": 0}

    class FakeExecutive:
        def __init__(self, base_dir):
            self.base_dir = base_dir

        def analizar_restaurante(self, core=None):
            called["analizar_restaurante"] += 1
            return {
                "ok": True,
                "estado": "fake",
                "datos_reales_modificados": False,
            }

        def analizar_evento(self, datos_evento):
            return {
                "ok": True,
                "estado": "fake_evento",
                "evento": dict(datos_evento or {}),
                "datos_reales_modificados": False,
            }

    monkeypatch.setattr(module, "HostAIExecutive", FakeExecutive)

    api = HostAIPlatformAPI(base_dir=tmp_path)
    response = api.handle(ApiRequest(method="GET", path="/api/v1/executive"))

    assert response.status_code == 200
    assert called["analizar_restaurante"] == 1
    assert response.payload.get("ok") is True
    assert response.payload.get("datos_reales_modificados") is False
    assert response.payload.get("executive", {}).get("estado") == "fake"


def test_get_api_v1_executive_error_homogeneo_sin_traceback(monkeypatch, tmp_path: Path) -> None:
    from API.facade import core_public_api02 as module

    class FailingExecutive:
        def __init__(self, base_dir):
            self.base_dir = base_dir

        def analizar_restaurante(self, core=None):
            raise RuntimeError("fallo interno C:\\ruta\\interna")

        def analizar_evento(self, datos_evento):
            raise RuntimeError("fallo interno")

    monkeypatch.setattr(module, "HostAIExecutive", FailingExecutive)

    api = HostAIPlatformAPI(base_dir=tmp_path)
    response = api.handle(ApiRequest(method="GET", path="/api/v1/executive"))

    assert response.status_code == 200
    payload = response.payload
    assert payload.get("ok") is False
    assert payload.get("version") == "1.0"
    assert payload.get("modo_seguro") is True
    assert payload.get("datos_reales_modificados") is False
    assert payload.get("error", {}).get("code") == "executive_unavailable"
    serialized = json.dumps(payload)
    assert "Traceback" not in serialized
    assert "C:\\\\" not in serialized
