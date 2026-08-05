from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from SERVICIOS.menu_necesidades_service import MenuNecesidadesService
from SERVICIOS.menus_inteligentes_service import MenusInteligentesService
from MOTORES.motor_compras import MotorCompras


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _seed(base: Path, *, stock: float = 1, linked: bool = True, recipe_unit: str = "kg", stock_unit: str = "kg") -> str:
    article_id = "ART-PATATA" if linked else None
    _write(base / "DATOS/db/escandallos_canonicos.json", {"escandallos": [{"receta": {
        "codigo": "REC-ENSALADILLA", "nombre": "Ensaladilla", "rendimiento": 4,
        "unidad_rendimiento": "raciones", "ingredientes": [{
            "nombre": "Patata", "articulo_id": article_id, "cantidad": 1, "unidad": recipe_unit,
        }],
    }}]})
    _write(base / "DATOS/db/articulos.json", [{
        "codigo": "ART-PATATA", "nombre": "Patata", "precio": 2, "unidad": "kg",
        "proveedor": "Proveedor A", "catalogo_maestro": {
            "proveedor_preferente": "Proveedor A", "unidad_compra": "saco",
            "cantidad_formato": "5", "unidad_base": "kg", "fecha_precio": "2026-07-01",
        },
    }])
    _write(base / "DATOS/db/proveedores.json", [])
    _write(base / "DATOS/db/compras_producto_proveedor.json", [])
    _write(base / "DATOS/db/stock_inicial.json", [{
        "codigo": "ART-PATATA", "articulo": "Patata", "stock_actual": stock, "unidad": stock_unit,
    }])
    _write(base / "DATOS/db/stock_movimientos.json", [])
    _write(base / "DATOS/facturas/historico_precios.json", {"registros": []})
    created = MenusInteligentesService(base).crear({
        "nombre": "Menú prueba", "estado": "BORRADOR", "comensales": 10,
        "secciones": [{"nombre": "Entrante", "elaboraciones": [{
            "elaboracion_id": "REC-ENSALADILLA", "cantidad": 1,
        }]}],
    })
    return created["menu"]["id"]


def test_necesidades_escala_por_rendimiento_cruza_stock_y_conserva_traza(tmp_path: Path) -> None:
    menu_id = _seed(tmp_path)
    result = MenuNecesidadesService(tmp_path).necesidades(menu_id)["necesidades"]
    line = result["lines"][0]

    assert line["cantidad_necesaria"] == 2.5
    assert line["stock_disponible"] == 1
    assert line["cantidad_faltante"] == 1.5
    assert line["estado"] == "Parcialmente cubierto"
    assert line["origenes"][0]["factor_escalado"] == 2.5
    assert line["cantidad_propuesta_compra"] == 5
    assert line["coste_estimado"] == 10


def test_ingrediente_sin_relacion_estable_es_visible_y_no_se_agrupa(tmp_path: Path) -> None:
    menu_id = _seed(tmp_path, linked=False)
    result = MenuNecesidadesService(tmp_path).necesidades(menu_id)["necesidades"]

    assert result["complete"] is False
    assert result["lines"][0]["estado"] == "Sin artículo relacionado"
    assert result["lines"][0]["cantidad_faltante"] is None
    assert result["blocking_errors"][0]["code"] == "UNRESOLVED_NEED"
    proposal = MenuNecesidadesService(tmp_path)
    # La línea pendiente se conserva en una propuesta revisable, no bloquea todo el flujo.
    pending = proposal.crear_propuesta(menu_id)["propuesta"]
    assert pending["resumen"]["articulos_pendientes"] == 1
    assert pending["lineas"][0]["estado"] == "Sin artículo relacionado"
    assert pending["lineas"][0]["cantidad_faltante"] is None


def test_conversion_incompatible_no_inventa_faltante(tmp_path: Path) -> None:
    menu_id = _seed(tmp_path, recipe_unit="u", stock_unit="kg")
    line = MenuNecesidadesService(tmp_path).necesidades(menu_id)["necesidades"]["lines"][0]

    assert line["estado"] == "Conversión pendiente"
    assert line["stock_disponible"] is None
    assert line["cantidad_faltante"] is None
    proposal = MenuNecesidadesService(tmp_path).crear_propuesta(menu_id)["propuesta"]
    assert proposal["lineas"][0]["estado"] == "Conversión pendiente"
    assert proposal["coste_completo"] is False


def test_api_genera_propuesta_y_crea_borrador_visible_en_compras_sin_modificar_stock(tmp_path: Path) -> None:
    menu_id = _seed(tmp_path, stock=0)
    stock_path = tmp_path / "DATOS/db/stock_inicial.json"
    before_stock = stock_path.read_bytes()
    client = TestClient(create_app(HostAIPlatformAPI(base_dir=tmp_path)))

    needs = client.get(f"/api/v1/menus/{menu_id}/necesidades")
    assert needs.status_code == 200
    assert needs.json()["necesidades"]["datos_reales_modificados"] is False
    proposal = client.post(f"/api/v1/menus/{menu_id}/propuesta-compra")
    assert proposal.status_code == 201
    body = proposal.json()["propuesta"]
    assert body["estado"] == "CONFIRMADA"
    assert body["grupos_proveedor"][0]["proveedor"] == "Proveedor A"
    assert body["resumen"]["articulos_propuestos"] == 1
    assert body["crea_pedido"] is True
    assert body["modifica_stock"] is False
    assert len(proposal.json()["pedidos_creados"]) == 1
    assert proposal.json()["pedidos_creados"][0]["estado"] == "borrador"
    assert menu_id in proposal.json()["pedidos_creados"][0]["observaciones"]
    assert stock_path.read_bytes() == before_stock
    persisted = json.loads((tmp_path / "DATOS/db/compras_pedidos.json").read_text(encoding="utf-8"))
    assert persisted[0]["id"] == proposal.json()["pedidos_creados"][0]["id"]

    dashboard = client.get("/api/v1/dashboard").json()
    assert any(order["id"] == persisted[0]["id"] for order in dashboard["dashboard"]["modulos"]["compras"]["pedidos"])

    fetched = client.get(f"/api/v1/menus/{menu_id}/propuesta-compra/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["propuesta"]["id"] == body["id"]


def test_stock_desconocido_y_proveedor_pendiente_no_bloquean_propuesta(tmp_path: Path) -> None:
    menu_id = _seed(tmp_path)
    _write(tmp_path / "DATOS/db/stock_inicial.json", [])
    articles = json.loads((tmp_path / "DATOS/db/articulos.json").read_text(encoding="utf-8"))
    articles[0]["proveedor"] = ""
    articles[0]["catalogo_maestro"]["proveedor_preferente"] = ""
    _write(tmp_path / "DATOS/db/articulos.json", articles)

    service = MenuNecesidadesService(tmp_path)
    needs = service.necesidades(menu_id)["necesidades"]
    assert needs["summary"]["compra_necesaria"] == 0
    assert needs["summary"]["candidatas_propuesta"] == 1
    proposal = service.crear_propuesta(menu_id)["propuesta"]
    assert proposal["resumen"] == {
        "articulos_propuestos": 0, "articulos_pendientes": 1, "proveedores_pendientes": 1,
    }
    assert proposal["lineas"][0]["estado"] == "Stock no disponible"


def test_revisa_propuesta_y_crea_borrador_idempotente_con_origen_sin_tocar_stock(tmp_path: Path) -> None:
    menu_id = _seed(tmp_path, stock=0)
    articles_path = tmp_path / "DATOS/db/articulos.json"
    articles = json.loads(articles_path.read_text(encoding="utf-8"))
    articles[0]["proveedor"] = ""
    articles[0]["catalogo_maestro"]["proveedor_preferente"] = ""
    _write(articles_path, articles)
    stock_path = tmp_path / "DATOS/db/stock_inicial.json"
    before_stock = stock_path.read_bytes()
    client = TestClient(create_app(HostAIPlatformAPI(base_dir=tmp_path)))
    proposal = client.post(f"/api/v1/menus/{menu_id}/propuesta-compra").json()["propuesta"]
    line = proposal["lineas"][0]
    reviewed = client.patch(f"/api/v1/menus/{menu_id}/propuesta-compra/{proposal['id']}", json={
        "version": proposal["version"], "lineas": [{
            "id": line["id"], "incluir": True, "cantidad_final_propuesta": 7,
            "proveedor": "Proveedor B", "observaciones": "Entregar por la mañana",
        }],
    })
    assert reviewed.status_code == 200
    reviewed_proposal = reviewed.json()["propuesta"]
    assert reviewed_proposal["lineas"][0]["cantidad_final_propuesta"] == 7

    created = client.post(f"/api/v1/menus/{menu_id}/propuesta-compra/{proposal['id']}/crear-pedidos", json={
        "confirmacion": "CREAR_BORRADORES", "usuario": "chef", "version": reviewed_proposal["version"],
    })
    assert created.status_code == 201
    order = created.json()["pedidos"][0]
    assert order["estado"] == "borrador"
    assert order["proveedor"] == "Proveedor B"
    assert order["lineas"][0]["cantidad"] == 7
    assert menu_id in order["observaciones"] and proposal["id"] in order["observaciones"]
    assert created.json()["stock_modificado"] is False
    assert created.json()["recepciones_creadas"] == 0
    assert created.json()["pedidos_creados"] == created.json()["pedidos"]
    assert len(created.json()["lineas_incluidas"]) == 1
    assert created.json()["lineas_pendientes"] == []
    assert created.json()["lineas_excluidas"] == []
    assert stock_path.read_bytes() == before_stock
    assert json.loads((tmp_path / "DATOS/db/compras_recepciones.json").read_text(encoding="utf-8")) == []

    repeated = client.post(f"/api/v1/menus/{menu_id}/propuesta-compra/{proposal['id']}/crear-pedidos", json={"confirmacion": "CREAR_BORRADORES", "version": reviewed_proposal["version"]})
    assert repeated.json()["pedidos"][0]["id"] == order["id"]
    persisted = json.loads((tmp_path / "DATOS/db/compras_pedidos.json").read_text(encoding="utf-8"))
    assert len(persisted) == 1


def test_crea_un_borrador_por_proveedor_y_separa_pendientes_y_excluidas(tmp_path: Path) -> None:
    menu_id = _seed(tmp_path, stock=0)
    service = MenuNecesidadesService(tmp_path)
    proposal = service.crear_propuesta(menu_id)["propuesta"]
    base = proposal["lineas"][0]
    proposal["lineas"] = [
        {**base, "id": "L-1", "proveedor": "Proveedor A", "cantidad_final_propuesta": 2},
        {**base, "id": "L-2", "proveedor": "Proveedor A", "cantidad_final_propuesta": 3},
        {**base, "id": "L-3", "proveedor": "Proveedor B", "cantidad_final_propuesta": 4},
        {**base, "id": "L-4", "proveedor": None, "cantidad_final_propuesta": 5},
        {**base, "id": "L-5", "incluir": False, "proveedor": "Proveedor C", "cantidad_final_propuesta": 6},
    ]

    result = service.crear_pedidos(menu_id, proposal["id"], {
        "confirmacion": "CREAR_BORRADORES", "version": proposal["version"], "usuario": "test",
    })

    assert result["ok"] is True
    assert [(order["proveedor"], len(order["lineas"])) for order in result["pedidos_creados"]] == [
        ("Proveedor A", 2), ("Proveedor B", 1),
    ]
    assert [line["id"] for line in result["lineas_incluidas"]] == ["L-1", "L-2", "L-3"]
    assert result["lineas_pendientes"][0]["id"] == "L-4"
    assert "Falta proveedor." in result["lineas_pendientes"][0]["motivos_pendientes"]
    assert result["lineas_excluidas"][0]["id"] == "L-5"
    assert all(order["estado"] == "borrador" for order in result["pedidos_creados"])


def test_rechaza_si_todas_las_lineas_estan_pendientes_y_no_crea_pedido(tmp_path: Path) -> None:
    menu_id = _seed(tmp_path, stock=0)
    service = MenuNecesidadesService(tmp_path)
    proposal = service.crear_propuesta(menu_id)["propuesta"]
    proposal["lineas"][0].update({"proveedor": None, "cantidad_final_propuesta": None})

    result = service.crear_pedidos(menu_id, proposal["id"], {
        "confirmacion": "CREAR_BORRADORES", "version": proposal["version"],
    })

    assert result["ok"] is False
    assert result["error"]["code"] == "no_orderable_lines"
    assert service.compras is None


def test_rechaza_propuesta_inexistente_y_version_obsoleta(tmp_path: Path) -> None:
    menu_id = _seed(tmp_path, stock=0)
    service = MenuNecesidadesService(tmp_path)
    missing = service.crear_pedidos(menu_id, "MENUPROP-INEXISTENTE", {
        "confirmacion": "CREAR_BORRADORES", "version": 1,
    })
    assert missing["error"]["code"] == "proposal_not_found"

    proposal = service.crear_propuesta(menu_id)["propuesta"]
    stale = service.crear_pedidos(menu_id, proposal["id"], {
        "confirmacion": "CREAR_BORRADORES", "version": proposal["version"] + 1,
    })
    assert stale["error"]["code"] == "proposal_version_conflict"
    assert service.compras is None


def test_motor_hace_rollback_si_falla_persistencia() -> None:
    class FailingDb:
        db_dir = Path(".")
        def cargar(self, _name): return []
        def guardar(self, _name, _rows): raise OSError("fallo simulado")

    motor = MotorCompras(FailingDb())
    try:
        motor.crear_pedidos_borrador_transaccional([{"proveedor": "Proveedor", "lineas": [{
            "nombre": "Patata", "articulo_id": "ART-1", "cantidad": 1, "unidad": "kg",
        }]}])
    except OSError as exc:
        assert "fallo simulado" in str(exc)
    else:
        raise AssertionError("Debía fallar la persistencia")
    assert motor.pedidos_sugeridos == {}
