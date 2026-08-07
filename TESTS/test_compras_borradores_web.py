import json
from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from MOTORES.motor_compras import MotorCompras
from SERVICIOS.base_datos_local import BaseDatosLocal
from SERVICIOS.compras_borradores_service import ComprasBorradoresService


def _seed(base: Path) -> str:
    motor = MotorCompras(BaseDatosLocal(base))
    motor.crear_proveedor_manual("Proveedor A")
    (base / "DATOS/db/articulos.json").write_text(json.dumps([{"codigo": "ART-1", "nombre": "Patata", "unidad": "kg", "precio": 3}]), encoding="utf-8")
    return motor.crear_pedidos_borrador_transaccional([{
        "proveedor": "Proveedor A", "origen_tipo": "menu", "origen_id": "MENU-1",
        "origen_version": 3, "propuesta_id": "PROP-1",
        "lineas": [{"nombre": "Patata", "articulo_id": "ART-1", "cantidad": 2, "unidad": "kg", "precio_unitario": 3}],
    }])[0]["id"]


def test_edita_borrador_persiste_y_no_crea_pedido_ni_stock(tmp_path: Path) -> None:
    pedido_id = _seed(tmp_path)
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))
    opened = client.get(f"/api/v1/compras/borradores/{pedido_id}")
    stock_path = tmp_path / "DATOS/db/stock_movimientos.json"
    stock_before = stock_path.read_bytes() if stock_path.exists() else None
    receptions_path = tmp_path / "DATOS/db/compras_recepciones.json"
    receptions_before = receptions_path.read_bytes() if receptions_path.exists() else None
    assert opened.status_code == 200
    assert opened.json()["borrador"]["origen"] == {"tipo": "menu", "id": "MENU-1", "version": 3, "propuesta_id": "PROP-1"}

    response = client.patch(f"/api/v1/compras/borradores/{pedido_id}", json={
        "proveedor": "Proveedor B", "observaciones": "Revisado",
        "lineas": [{"nombre": "Patata", "articulo_id": "ART-1", "cantidad": 4, "unidad": "kg", "precio_unitario": 3}, {"nombre": "Cebolla", "cantidad": 1, "unidad": "kg", "precio_unitario": 2}],
    })
    assert response.status_code == 200
    draft = response.json()["borrador"]
    assert draft["estado"] == "borrador"
    assert draft["proveedor"] == "Proveedor B"
    assert draft["importe_estimado"] == 14
    assert len(draft["lineas"]) == 2
    reopened = client.get(f"/api/v1/compras/borradores/{pedido_id}").json()["borrador"]
    assert reopened["lineas"] == draft["lineas"]
    assert (stock_path.read_bytes() if stock_path.exists() else None) == stock_before
    assert (receptions_path.read_bytes() if receptions_path.exists() else None) == receptions_before


def test_borrador_rechaza_cantidad_invalida_y_pedido_no_borrador(tmp_path: Path) -> None:
    pedido_id = _seed(tmp_path)
    motor = MotorCompras(BaseDatosLocal(tmp_path))
    try:
        motor.actualizar_borrador_completo(pedido_id, {"proveedor": "A", "lineas": [{"nombre": "X", "unidad": "kg", "cantidad": 0}]})
        assert False
    except ValueError as exc:
        assert "mayor que cero" in str(exc)
    motor.cambiar_estado_pedido(pedido_id, "preparado")
    try:
        motor.actualizar_borrador_completo(pedido_id, {"proveedor": "A", "lineas": []})
        assert False
    except ValueError as exc:
        assert "estado borrador" in str(exc)


def test_confirma_borrador_como_preparado_idempotente_y_sin_recepcion_ni_stock(tmp_path: Path) -> None:
    pedido_id = _seed(tmp_path)
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))
    opened = client.get(f"/api/v1/compras/borradores/{pedido_id}").json()
    assert opened["revision"]["valido"] is True
    stock_path = tmp_path / "DATOS/db/stock_movimientos.json"
    receptions_path = tmp_path / "DATOS/db/compras_recepciones.json"
    stock_before = stock_path.read_bytes()
    receptions_before = receptions_path.read_bytes()

    response = client.post(f"/api/v1/compras/borradores/{pedido_id}/confirmar", json={
        "confirmacion": "CONFIRMAR_PEDIDO", "usuario": "chef", "actualizado_en": opened["borrador"]["actualizado_en"],
    })
    assert response.status_code == 200
    body = response.json()
    assert body["pedido"]["estado"] == "preparado"
    assert body["pedido"]["borrador_origen_id"] == pedido_id
    assert body["pedido"]["confirmado_por"] == "chef"
    assert body["pedido"]["origen"] == {"tipo": "menu", "id": "MENU-1", "version": 3, "propuesta_id": "PROP-1"}
    assert any(item["accion"] == "pedido_confirmado" for item in body["pedido"]["historial"])
    assert body["stock_modificado"] is False and body["inventario_modificado"] is False
    assert body["recepciones_creadas"] == 0
    assert stock_path.read_bytes() == stock_before
    assert receptions_path.read_bytes() == receptions_before

    repeated = client.post(f"/api/v1/compras/borradores/{pedido_id}/confirmar", json={"confirmacion": "CONFIRMAR_PEDIDO", "usuario": "chef"})
    assert repeated.status_code == 200
    assert repeated.json()["idempotente"] is True
    assert repeated.json()["pedido"]["id"] == pedido_id


def test_confirmacion_rechaza_borradores_incompletos_y_version_obsoleta(tmp_path: Path) -> None:
    pedido_id = _seed(tmp_path)
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))
    opened = client.get(f"/api/v1/compras/borradores/{pedido_id}").json()["borrador"]
    invalid = client.patch(f"/api/v1/compras/borradores/{pedido_id}", json={
        "proveedor": "Proveedor inexistente", "lineas": [{"nombre": "Patata", "articulo_id": "NO-EXISTE", "cantidad": 2, "unidad": "kg", "precio_unitario": 0}],
    })
    assert invalid.status_code == 200
    confirmation = client.post(f"/api/v1/compras/borradores/{pedido_id}/confirmar", json={"confirmacion": "CONFIRMAR_PEDIDO", "actualizado_en": invalid.json()["borrador"]["actualizado_en"]})
    assert confirmation.status_code == 400
    assert {item["code"] for item in confirmation.json()["revision"]["errores_bloqueantes"]} == {"invalid_provider", "invalid_article"}
    assert confirmation.json()["revision"]["advertencias"][0]["code"] == "price_pending"
    assert client.get(f"/api/v1/compras/borradores/{pedido_id}").json()["borrador"]["estado"] == "borrador"

    restored = client.patch(f"/api/v1/compras/borradores/{pedido_id}", json={
        "proveedor": "Proveedor A", "lineas": [{"nombre": "Patata", "articulo_id": "ART-1", "cantidad": 2, "unidad": "kg", "precio_unitario": 3}],
    }).json()["borrador"]
    conflict = client.post(f"/api/v1/compras/borradores/{pedido_id}/confirmar", json={"confirmacion": "CONFIRMAR_PEDIDO", "actualizado_en": "version-obsoleta"})
    assert restored["estado"] == "borrador"
    assert conflict.status_code == 409


def test_confirmacion_hace_rollback_si_falla_persistencia() -> None:
    motor = MotorCompras()
    pedido = motor.crear_pedidos_borrador_transaccional([{"proveedor": "Proveedor A", "lineas": [{"nombre": "Patata", "articulo_id": "ART-1", "cantidad": 1, "unidad": "kg"}]}])[0]
    class FailingDb:
        def guardar(self, *_args, **_kwargs):
            raise OSError("fallo simulado")
    motor.db = FailingDb()
    try:
        motor.confirmar_borrador_pedido(pedido["id"], usuario="chef")
        assert False
    except OSError:
        pass
    assert motor.obtener_pedido(pedido["id"]).estado == "borrador"


def test_validacion_final_bloquea_linea_vacia_y_cantidad_cero(tmp_path: Path) -> None:
    pedido_id = _seed(tmp_path)
    motor = MotorCompras(BaseDatosLocal(tmp_path))
    service = ComprasBorradoresService(motor, tmp_path)
    pedido = motor.obtener_pedido(pedido_id)
    original_line = pedido.lineas[0]

    pedido.lineas = []
    empty = service.confirmar(pedido_id, {"confirmacion": "CONFIRMAR_PEDIDO", "usuario": "chef"})
    assert empty["ok"] is False
    assert empty["revision"]["errores_bloqueantes"][0]["code"] == "empty_order"

    pedido.lineas = [original_line]
    pedido.lineas[0].cantidad = 0
    zero = service.confirmar(pedido_id, {"confirmacion": "CONFIRMAR_PEDIDO", "usuario": "chef"})
    assert zero["ok"] is False
    assert any(item["code"] == "invalid_quantity" for item in zero["revision"]["errores_bloqueantes"])
