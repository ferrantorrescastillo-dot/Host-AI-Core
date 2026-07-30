from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app


def test_dashboard_ofrece_los_cuatro_modulos_para_la_vista_executive(
    tmp_path: Path,
) -> None:
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))

    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    modules = payload["dashboard"]["modulos"]
    assert {"compras", "eventos", "produccion", "stock"} <= modules.keys()
    assert payload["datos_reales_modificados"] is False


def test_dashboard_devuelve_colecciones_vacias_sin_inventar_datos(
    tmp_path: Path,
) -> None:
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))

    modules = client.get("/api/v1/dashboard").json()["dashboard"]["modulos"]

    assert modules["compras"]["items"] == []
    assert modules["eventos"]["items"] == []
    assert modules["produccion"]["items"] == []
    assert modules["stock"]["items"] == []
