from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from MOTORES.motor_compras import MotorCompras
from SERVICIOS.base_datos_local import BaseDatosLocal


def _seed(base: Path) -> str:
    motor = MotorCompras(BaseDatosLocal(base))
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
