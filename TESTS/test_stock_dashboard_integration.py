from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from CORE.host_ai_core import HostAICore
from SERVICIOS.host_ai_home_read_service import HostAIHomeReadService


def _write_stock(base_dir: Path) -> None:
    db = base_dir / "DATOS" / "db"
    db.mkdir(parents=True, exist_ok=True)
    (db / "stock_lotes.json").write_text(
        json.dumps(
            [
                {
                    "id": "LOTE-WEB-1",
                    "articulo_id": "ART-TOMATE",
                    "nombre": "Tomate",
                    "cantidad": 4,
                    "unidad": "kg",
                    "familia": "Verduras",
                    "ubicacion": "Camara",
                    "proveedor": "Proveedor Uno",
                    "fecha_entrada": "2099-01-01",
                    "caducidad": date.today().isoformat(),
                    "coste_unitario": 2.5,
                    "creado_en": "2099-01-01T10:00:00",
                }
            ]
        ),
        encoding="utf-8",
    )
    (db / "stock_movimientos.json").write_text(
        json.dumps(
            [
                {
                    "id": "MOV-WEB-1",
                    "tipo": "entrada",
                    "articulo_id": "ART-TOMATE",
                    "nombre": "Tomate",
                    "cantidad": 4,
                    "unidad": "kg",
                    "motivo": "Recepcion",
                    "lote_id": "LOTE-WEB-1",
                    "trazabilidad": {},
                    "creado_en": "2099-01-01T10:00:00",
                }
            ]
        ),
        encoding="utf-8",
    )


def test_home_stock_expone_datos_reales(tmp_path: Path) -> None:
    _write_stock(tmp_path)
    core = HostAICore(tmp_path)
    core.stock.ajustar_minimo("Tomate", 6, articulo_id="ART-TOMATE")

    modulo = HostAIHomeReadService(core).cargar_home()["modulos"]["stock"]

    assert modulo["estado"] == "datos_disponibles"
    assert modulo["total"] == 2
    assert modulo["total_existencias"] == 1
    assert modulo["total_lotes"] == 1
    assert modulo["total_movimientos"] == 1
    assert modulo["total_alertas"] == 2
    assert modulo["estado_operativo"] == "revisar"
    assert modulo["total_caducidades"] == 1
    assert modulo["existencias"][0]["cantidad"] == 4
    assert modulo["lotes"][0]["id"] == "LOTE-WEB-1"
    assert modulo["movimientos"][0]["id"] == "MOV-WEB-1"
    assert {item["tipo"] for item in modulo["alertas"]} == {
        "bajo_stock",
        "caducidad_cercana",
    }


def test_home_stock_sin_datos_conserva_contrato(tmp_path: Path) -> None:
    modulo = HostAIHomeReadService(HostAICore(tmp_path)).cargar_home()["modulos"]["stock"]

    assert modulo["estado"] == "sin_datos"
    assert modulo["total"] == 0
    assert modulo["items"] == []
    assert modulo["existencias"] == []
    assert modulo["lotes"] == []
    assert modulo["movimientos"] == []
    assert modulo["caducidades"] == []
    assert modulo["resumen"]["articulos"] == 0


def test_home_stock_error_controlado(monkeypatch, tmp_path: Path) -> None:
    core = HostAICore(tmp_path)

    def fail():
        raise RuntimeError("fallo interno")

    monkeypatch.setattr(core.stock, "stock_actual", fail)
    modulo = HostAIHomeReadService(core).cargar_home()["modulos"]["stock"]

    assert modulo["estado"] == "error_parcial"
    assert modulo["total"] == 0
    assert modulo["items"] == []
    assert modulo["mensaje"] == "Error de lectura del modulo."


def test_http_dashboard_expone_contrato_stock(tmp_path: Path) -> None:
    _write_stock(tmp_path)
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))

    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    modulo = response.json()["dashboard"]["modulos"]["stock"]
    assert modulo["total_existencias"] == 1
    assert modulo["total_lotes"] == 1
    assert modulo["total_movimientos"] == 1
    assert modulo["total_caducidades"] == 1
    assert modulo["existencias"][0]["nombre"] == "Tomate"
    assert modulo["lotes"][0]["caducidad"] == date.today().isoformat()
    assert modulo["movimientos"][0]["tipo"] == "entrada"
