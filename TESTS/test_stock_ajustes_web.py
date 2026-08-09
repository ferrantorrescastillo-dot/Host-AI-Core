from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from CORE.host_ai_core import HostAICore
from SERVICIOS.stock_ajustes_service import StockAjustesService


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _seed(base: Path) -> tuple[HostAICore, StockAjustesService]:
    _write(base / "DATOS/db/articulos.json", [{"codigo": "ART-PATATA", "nombre": "Patata Monalisa", "unidad": "kg", "familia": "Verduras", "precio": 1}])
    for name in ("stock_lotes", "stock_movimientos"):
        _write(base / f"DATOS/db/{name}.json", [])
    core = HostAICore(base)
    return core, StockAjustesService(core)


def _body(kind: str, quantity: float, **extra: object) -> dict[str, object]:
    return {"article_id": "ART-PATATA", "tipo": kind, "cantidad": quantity, "unidad": "kg",
            "confirmacion": "REGISTRAR_MOVIMIENTO_STOCK", "usuario": "chef", "observaciones": "Conteo manual", **extra}


def test_inventario_inicial_crea_lote_movimiento_y_persiste(tmp_path: Path) -> None:
    core, service = _seed(tmp_path)
    result = service.registrar(_body("INVENTARIO_INICIAL", 0.5, lote="L-1", ubicacion="Cámara", caducidad="2026-09-01"))
    assert result["ok"] is True and result["stock_actual"] == 0.5
    assert result["movimiento"]["tipo"] == "inventario_inicial"
    assert result["movimiento"]["signo"] == 1 and result["movimiento"]["usuario"] == "chef"
    assert result["movimiento"]["trazabilidad"]["lote"] == "L-1"
    reloaded = HostAICore(tmp_path)
    assert reloaded.stock.predecir_necesidad("Patata Monalisa", 0.75, "kg", "ART-PATATA")["cantidad_faltante"] == 0.25
    assert len(reloaded.stock.movimientos) == 1


def test_ajustes_positivo_y_negativo_recalculan_desde_movimientos(tmp_path: Path) -> None:
    core, service = _seed(tmp_path)
    service.registrar(_body("INVENTARIO_INICIAL", 0.5))
    positive = service.registrar(_body("AJUSTE_POSITIVO", 0.5))
    assert positive["stock_actual"] == 1
    assert core.stock.predecir_necesidad("Patata Monalisa", 0.75, "kg", "ART-PATATA")["cantidad_faltante"] == 0
    negative = service.registrar(_body("AJUSTE_NEGATIVO", 0.25))
    assert negative["stock_actual"] == 0.75
    assert [movement.tipo for movement in core.stock.movimientos.values()] == ["inventario_inicial", "ajuste_positivo", "ajuste_negativo"]


def test_validaciones_bloquean_sin_escribir(tmp_path: Path) -> None:
    core, service = _seed(tmp_path)
    for body, code in [
        (_body("AJUSTE_POSITIVO", 0), "invalid_quantity"),
        ({**_body("AJUSTE_POSITIVO", 1), "article_id": "NO-EXISTE"}, "article_not_found"),
        ({**_body("AJUSTE_POSITIVO", 1), "unidad": "l"}, "invalid_unit"),
        (_body("AJUSTE_NEGATIVO", 1), "negative_stock_blocked"),
    ]:
        assert service.registrar(body)["error"]["code"] == code
    assert not core.stock.movimientos and not core.stock.lotes


def test_inventario_existente_exige_confirmacion_y_corrige_con_movimiento(tmp_path: Path) -> None:
    core, service = _seed(tmp_path)
    service.registrar(_body("INVENTARIO_INICIAL", 1))
    denied = service.registrar(_body("INVENTARIO_INICIAL", 0.6))
    assert denied["error"]["code"] == "initial_inventory_exists"
    corrected = service.registrar(_body("INVENTARIO_INICIAL", 0.6, confirmar_existente=True))
    assert corrected["stock_actual"] == 0.6
    assert corrected["movimiento"]["tipo"] == "ajuste_negativo"
    assert len(core.stock.movimientos) == 2


def test_endpoint_no_crea_pedidos_recepciones_ni_produccion(tmp_path: Path) -> None:
    _seed(tmp_path)
    client = TestClient(create_app(HostAIPlatformAPI(base_dir=tmp_path)))
    response = client.post("/api/v1/stock/movimientos", json=_body("INVENTARIO_INICIAL", 1, production_plan_id="PLAN-1", return_to="produccion"))
    assert response.status_code == 201
    payload = response.json()
    assert payload["pedidos_creados"] == 0 and payload["recepciones_creadas"] == 0
    assert payload["movimiento"]["trazabilidad"]["production_plan_id"] == "PLAN-1"
