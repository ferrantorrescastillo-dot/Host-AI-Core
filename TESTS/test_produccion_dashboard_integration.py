from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from CORE.host_ai_core import HostAICore
from SERVICIOS.host_ai_home_read_service import HostAIHomeReadService


def _write_plan(base_dir: Path) -> None:
    db = base_dir / "DATOS" / "db"
    db.mkdir(parents=True, exist_ok=True)
    (db / "planes_produccion.json").write_text(
        json.dumps(
            [
                {
                    "id": "PLAN-WEB-1",
                    "evento_id": "EVT-WEB-1",
                    "evento": "Boda Web",
                    "nombre": "Produccion Boda Web",
                    "fecha": "2099-08-02",
                    "pax": 120,
                    "responsable": "Jefa de cocina",
                    "estado": "activo",
                    "avisos": ["Revisar tiempos de abatido."],
                    "tareas": [
                        {
                            "id": "TAREA-WEB-1",
                            "titulo": "Preparar fondo",
                            "cantidad": 12,
                            "unidad": "l",
                            "estado_ejecucion": "bloqueada",
                            "bloqueo": "Falta marmita",
                            "incidencias": [{"id": "INC-1", "descripcion": "Falta marmita"}],
                        },
                        {
                            "id": "TAREA-WEB-2",
                            "titulo": "Cortar verduras",
                            "cantidad": 20,
                            "unidad": "kg",
                            "estado_ejecucion": "pendiente",
                        },
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )


def test_home_produccion_expone_datos_reales(tmp_path: Path) -> None:
    _write_plan(tmp_path)
    modulo = HostAIHomeReadService(HostAICore(tmp_path)).cargar_home()["modulos"]["produccion"]

    assert modulo["estado"] == "datos_disponibles"
    assert modulo["total"] == 1
    assert modulo["planes_activos"] == 1
    assert modulo["total"] == len(modulo["items"])
    assert modulo["planes_activos"] == len(modulo["items"])
    assert modulo["total_tareas"] == 2
    assert modulo["tareas_pendientes"] == 1
    assert modulo["tareas_bloqueadas"] == 1
    assert modulo["resumen"]["alertas"] >= 1
    assert modulo["resumen"]["tareas"] == modulo["total_tareas"]
    assert modulo["resumen"]["pendientes"] == modulo["tareas_pendientes"]
    assert modulo["items"][0]["id"] == "PLAN-WEB-1"
    assert modulo["items"][0]["tareas"][0]["bloqueo"] == "Falta marmita"


def test_home_produccion_sin_datos_conserva_contrato(tmp_path: Path) -> None:
    modulo = HostAIHomeReadService(HostAICore(tmp_path)).cargar_home()["modulos"]["produccion"]

    assert modulo["estado"] == "sin_datos"
    assert modulo["total"] == 0
    assert modulo["items"] == []
    assert modulo["resumen"]["planes_activos"] == 0
    assert modulo["resumen"]["tareas"] == 0


def test_home_produccion_error_controlado(monkeypatch, tmp_path: Path) -> None:
    core = HostAICore(tmp_path)
    monkeypatch.setattr(core.produccion_real, "listar_planes", lambda: (_ for _ in ()).throw(RuntimeError("fallo interno")))

    result = HostAIHomeReadService(core).cargar_home()
    modulo = result["modulos"]["produccion"]

    assert modulo["estado"] == "error_parcial"
    assert modulo["total"] == 0
    assert modulo["items"] == []
    assert modulo["mensaje"] == "Error de lectura del modulo."


def test_http_dashboard_expone_contrato_produccion(tmp_path: Path) -> None:
    _write_plan(tmp_path)
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))

    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    modulo = response.json()["dashboard"]["modulos"]["produccion"]
    assert modulo["total"] == 1
    assert modulo["resumen"]["tareas"] == 2
    assert modulo["items"][0]["evento_id"] == "EVT-WEB-1"
    assert modulo["items"][0]["tareas"][1]["titulo"] == "Cortar verduras"
