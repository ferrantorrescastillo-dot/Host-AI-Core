from __future__ import annotations

import json
from pathlib import Path

from API.app import HostAIPlatformAPI
from API.contracts.http_models import ApiRequest


def _write_compras_fixture(base_dir: Path) -> None:
    db_dir = base_dir / "DATOS" / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    fixtures = {
        "compras_propuestas.json": [
            {
                "id": "PROP-1",
                "producto": "Tomate",
                "necesario": 8,
                "disponible": 3,
                "comprar": 5,
                "unidad": "kg",
                "origen": "Test",
                "prioridad": "Alta",
                "estado": "pendiente",
            }
        ],
        "compras_proveedores.json": [
            {"id": "PROV-1", "nombre": "Proveedor Uno", "estado": "activo"}
        ],
        "compras_registros.json": [
            {
                "id": "COMPRA-1",
                "producto": "Tomate",
                "cantidad": 5,
                "unidad": "kg",
                "proveedor": "Proveedor Uno",
                "estado": "registrada",
            }
        ],
    }
    for name, content in fixtures.items():
        (db_dir / name).write_text(json.dumps(content), encoding="utf-8")


def _write_eventos_fixture(base_dir: Path) -> None:
    db_dir = base_dir / "DATOS" / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    (db_dir / "eventos.json").write_text(
        json.dumps(
            [
                {
                    "id": "EVT-WEB-1",
                    "nombre": "Boda Web",
                    "fecha": "2099-08-02",
                    "pax": 120,
                    "estado": "confirmado",
                    "servicios": [
                        {
                            "id": "SERV-WEB-1",
                            "nombre": "Cena",
                            "tipo": "cena",
                            "hora_inicio": "20:00",
                            "duracion_min": 240,
                            "pases": [],
                        }
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )


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


def test_get_api_v1_dashboard_expone_resumen_compras_real(tmp_path: Path) -> None:
    _write_compras_fixture(tmp_path)

    api = HostAIPlatformAPI(base_dir=tmp_path)
    response = api.handle(ApiRequest(method="GET", path="/api/v1/dashboard"))

    compras = response.payload["dashboard"]["modulos"]["compras"]
    assert compras["necesidades_pendientes"] == 0
    assert compras["propuestas_pendientes"] == 1
    assert compras["total_propuestas"] == 1
    assert compras["total_proveedores"] == 1
    assert compras["total_historial"] == 1
    assert compras["propuestas"][0]["id"] == "PROP-1"
    assert compras["proveedores"][0]["id"] == "PROV-1"
    assert compras["historial"][0]["id"] == "COMPRA-1"


def test_get_api_v1_dashboard_expone_resumen_eventos_real(tmp_path: Path) -> None:
    _write_eventos_fixture(tmp_path)

    api = HostAIPlatformAPI(base_dir=tmp_path)
    response = api.handle(ApiRequest(method="GET", path="/api/v1/dashboard"))

    eventos = response.payload["dashboard"]["modulos"]["eventos"]
    assert eventos["estado"] == "datos_disponibles"
    assert eventos["total"] == 1
    assert eventos["eventos_activos"] == 1
    assert eventos["total_servicios"] == 1
    assert eventos["total_avisos"] == 1
    assert eventos["resumen"]["pax_total"] == 120
    assert eventos["items"][0]["id"] == "EVT-WEB-1"
    assert eventos["items"][0]["estado"] == "confirmado"
    assert eventos["items"][0]["avisos"] == ["Hay servicios sin pases."]


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
