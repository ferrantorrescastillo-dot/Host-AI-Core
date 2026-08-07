from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from CORE.host_ai_core import HostAICore
from SERVICIOS.menu_produccion_service import MenuProduccionService
from SERVICIOS.menu_necesidades_service import MenuNecesidadesService
from SERVICIOS.menus_inteligentes_service import MenusInteligentesService


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _seed(base: Path, stock: float = 10) -> tuple[HostAICore, str]:
    _write(base / "DATOS/db/escandallos_canonicos.json", {"escandallos": [{"receta": {
        "codigo": "REC-ENS", "nombre": "Ensaladilla", "rendimiento": 4, "unidad_rendimiento": "raciones",
        "ingredientes": [{"nombre": "Patata", "articulo_id": "ART-PATATA", "cantidad": 1, "unidad": "kg"}],
    }}]})
    _write(base / "DATOS/db/articulos.json", [{"codigo": "ART-PATATA", "nombre": "Patata", "unidad": "kg", "precio": 2, "proveedor": "Proveedor A"}])
    _write(base / "DATOS/db/stock_inicial.json", [{"codigo": "ART-PATATA", "articulo": "Patata", "stock_actual": stock, "unidad": "kg"}])
    for name, value in {"stock_lotes": [], "stock_movimientos": [], "planes_produccion": [], "escandallos": []}.items():
        _write(base / f"DATOS/db/{name}.json", value)
    menu = MenusInteligentesService(base).crear({"nombre": "Menú 10 pax", "comensales": 10, "secciones": [{"nombre": "Principal", "elaboraciones": [{"elaboracion_id": "REC-ENS", "cantidad": 1}]}]})["menu"]
    core = HostAICore(base)
    core.stock.registrar_entrada("Patata", stock, "kg", articulo_id="ART-PATATA", motivo="fixture")
    return core, menu["id"]


def test_genera_plan_escalado_agrupado_y_no_modifica_stock(tmp_path: Path) -> None:
    core, menu_id = _seed(tmp_path)
    before = [(x.id, x.cantidad) for x in core.stock.lotes.values()]
    service = MenuProduccionService(core)
    result = service.generar(menu_id, {"fecha_servicio": "2026-09-01", "event_id": "EV-1"})
    plan = result["plan"]

    assert result["stock_modificado"] is False
    assert plan["menu_id"] == menu_id and plan["menu_version"] == 1
    assert plan["event_id"] if "event_id" in plan else plan["evento_id"] == "EV-1"
    assert plan["comensales"] == 10
    assert plan["elaboraciones"][0]["cantidad_a_producir"] == 10
    assert plan["elaboraciones"][0]["factor_escalado"] == 2.5
    assert plan["ingredientes"][0]["cantidad"] == 2.5
    assert [(x.id, x.cantidad) for x in core.stock.lotes.values()] == before
    assert service.generar(menu_id, {})["idempotente"] is True


def test_plan_persiste_reabre_y_no_genera_movimientos(tmp_path: Path) -> None:
    core, menu_id = _seed(tmp_path)
    service = MenuProduccionService(core)
    plan = service.generar(menu_id, {})["plan"]
    movements_before = [item.to_dict() for item in core.stock.movimientos.values()]
    reopened = MenuProduccionService(HostAICore(tmp_path)).obtener(plan["id"])["plan"]
    assert reopened["menu_id"] == menu_id
    assert reopened["elaboraciones"][0]["cantidad_a_producir"] == 10
    assert reopened["solo_planificacion"] is True
    assert [item.to_dict() for item in core.stock.movimientos.values()] == movements_before


def test_stock_insuficiente_bloquea_plan_sin_consumo(tmp_path: Path) -> None:
    core, menu_id = _seed(tmp_path, stock=1)
    before = len(core.stock.movimientos)
    service = MenuProduccionService(core)
    plan = service.generar(menu_id, {})["plan"]
    assert plan["estado"] == "BLOQUEADO"
    assert plan["elaboraciones"][0]["estado"] == "BLOQUEADO"
    assert plan["ingredientes"][0]["faltante"] == 0.5
    assert len(core.stock.movimientos) == before


def test_http_expone_solo_planificacion(tmp_path: Path) -> None:
    _core, menu_id = _seed(tmp_path, stock=1)
    client = TestClient(create_app(HostAIPlatformAPI(base_dir=tmp_path)))
    created = client.post(f"/api/v1/menus/{menu_id}/plan-produccion", json={})
    assert created.status_code == 201
    plan = created.json()["plan"]
    assert client.get(f"/api/v1/produccion/planes/{plan['id']}").status_code == 200
    task_id = plan["elaboraciones"][0]["id"]
    assert client.get(f"/api/v1/produccion/planes/{plan['id']}/tareas/{task_id}/consumo-previsto").status_code == 404
    assert client.post(f"/api/v1/produccion/planes/{plan['id']}/tareas/{task_id}/confirmar", json={}).status_code == 404
    proposal = client.post(f"/api/v1/produccion/planes/{plan['id']}/propuesta-compra", json={})
    assert proposal.status_code == 200
    assert proposal.json()["propuesta"]["origen"] == "produccion"
    assert proposal.json()["pedidos_creados"] == []


def test_subelaboraciones_detectan_ciclo_y_bloquean_plan(tmp_path: Path) -> None:
    core, menu_id = _seed(tmp_path)
    _write(tmp_path / "DATOS/db/escandallos_canonicos.json", {"escandallos": [
        {"receta": {"codigo": "REC-ENS", "nombre": "Ensaladilla", "rendimiento": 4, "ingredientes": [{"nombre": "Salsa", "elaboracion_id": "REC-SALSA", "cantidad": 1, "unidad": "kg"}]}},
        {"receta": {"codigo": "REC-SALSA", "nombre": "Salsa", "rendimiento": 1, "ingredientes": [{"nombre": "Ensaladilla", "elaboracion_id": "REC-ENS", "cantidad": 1, "unidad": "kg"}]}},
    ]})
    service = MenuProduccionService(core)
    # Los lectores de escandallo se inicializan con el servicio y ven el ciclo real.
    plan = service.generar(menu_id, {})["plan"]
    assert any(error["code"] == "PRODUCTION_CYCLE" for error in plan["errores_bloqueantes"])
    assert plan["estado"] == "BLOQUEADO"


def test_agrupa_subelaboracion_compartida_con_trazabilidad() -> None:
    aggregated: dict[tuple[str, str], dict] = {}
    for task, quantity in [({"receta_id": "REC-A", "titulo": "Plato A"}, 2), ({"receta_id": "REC-B", "titulo": "Plato B"}, 3)]:
        MenuProduccionService._collect_subelaborations({"componentes": [{
            "tipo": "elaboracion", "nombre": "Salsa de cava", "receta_referenciada_id": "REC-SALSA",
            "cantidad_necesaria": quantity, "unidad": "l", "detalle": {"componentes": []},
        }]}, task, aggregated)
    salsa = aggregated[("REC-SALSA", "l")]
    assert salsa["cantidad_a_producir"] == 5
    assert {origin["elaboracion_id"] for origin in salsa["origenes"]} == {"REC-A", "REC-B"}


def test_propuesta_produccion_filtra_pendientes_y_es_idempotente(tmp_path: Path) -> None:
    class ComprasNoInvocable:
        def __getattr__(self, name: str):
            raise AssertionError(f"Producción no debe invocar MotorCompras.{name}")

    service = MenuNecesidadesService(tmp_path, compras=ComprasNoInvocable())
    lines = [
        {"articulo_id": "ART-1", "articulo_nombre": "Patata", "ingrediente_nombre": "Patata", "cantidad_necesaria": 5, "cantidad_faltante": 2, "unidad_necesaria": "kg", "estado": "Compra necesaria", "proveedor_preferente": "P1", "cantidad_propuesta_compra": 2, "coste_estimado": 4},
        {"articulo_id": "ART-2", "articulo_nombre": "Sal", "ingrediente_nombre": "Sal", "cantidad_necesaria": 1, "cantidad_faltante": None, "unidad_necesaria": "kg", "estado": "Stock no disponible"},
        {"articulo_id": None, "articulo_nombre": None, "ingrediente_nombre": "Especia", "cantidad_necesaria": 1, "cantidad_faltante": None, "unidad_necesaria": "g", "estado": "Sin artículo relacionado"},
        {"articulo_id": "ART-3", "articulo_nombre": "Leche", "ingrediente_nombre": "Leche", "cantidad_necesaria": 2, "cantidad_faltante": None, "unidad_necesaria": "l", "estado": "Conversión pendiente"},
    ]
    service.necesidades = lambda _menu_id: {"ok": True, "necesidades": {"menu_version": 3, "lines": lines}}  # type: ignore[method-assign]
    trace = {"production_plan_id": "PLAN-1", "event_id": "EV-1", "fecha": "2026-09-01"}
    first = service.crear_propuesta_faltantes_produccion("MENU-1", trace)
    repeated = service.crear_propuesta_faltantes_produccion("MENU-1", trace)
    assert [line["articulo_id"] for line in first["propuesta"]["lineas"]] == ["ART-1"]
    assert first["propuesta"]["production_plan_id"] == "PLAN-1"
    assert first["propuesta"]["menu_version"] == 3 and first["propuesta"]["event_id"] == "EV-1"
    assert first["propuesta"]["crea_pedido"] is False and first["stock_modificado"] is False
    assert repeated["idempotente"] is True and repeated["propuesta"]["id"] == first["propuesta"]["id"]
