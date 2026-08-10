import json
from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from MOTORES.motor_compras import MotorCompras
from SERVICIOS.base_datos_local import BaseDatosLocal


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _seed(base: Path, *, article_id: str = "ART-1", unit: str = "kg") -> tuple[TestClient, str]:
    _write(base / "DATOS/db/articulos.json", [{"codigo": "ART-1", "nombre": "Patata Monalisa", "unidad": "kg", "precio": 2}])
    motor = MotorCompras(BaseDatosLocal(base)); motor.crear_proveedor_manual("Proveedor A")
    order = motor.crear_pedidos_borrador_transaccional([{"proveedor": "Proveedor A", "lineas": [{"nombre": "Patata Monalisa", "articulo_id": article_id, "cantidad": 10, "unidad": unit, "precio_unitario": 2}]}])[0]
    motor.confirmar_borrador_pedido(order["id"], usuario="test")
    return TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=base))), order["id"]


def test_borrador_desde_pedido_no_modifica_stock_y_conserva_contrato(tmp_path: Path) -> None:
    client, order_id = _seed(tmp_path)
    stock_path = tmp_path / "DATOS/db/stock_movimientos.json"; before = stock_path.read_bytes()
    response = client.post(f"/api/v1/compras/pedidos/{order_id}/recepciones", json={})
    assert response.status_code == 201
    reception = response.json()["recepcion"]
    assert reception["estado"] == "BORRADOR" and reception["order_id"] == order_id
    assert reception["proveedor"] == "Proveedor A" and reception["document_type"] == "albaran"
    assert reception["lineas"][0]["ordered_quantity"] == 10
    assert reception["lineas"][0]["previously_received"] == 0
    assert reception["lineas"][0]["pending_quantity"] == 10
    assert stock_path.read_bytes() == before


def test_dashboard_expone_pedido_preparado_como_recepcionable(tmp_path: Path) -> None:
    client, order_id = _seed(tmp_path)
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    pedidos = response.json()["dashboard"]["modulos"]["compras"]["pedidos"]
    pedido = next(item for item in pedidos if item["id"] == order_id)
    assert pedido["estado"] == "preparado"
    assert pedido["lineas"][0]["nombre"] == "Patata Monalisa"


def test_recepcion_parcial_y_segunda_recepcion_completan_sin_duplicar(tmp_path: Path) -> None:
    client, order_id = _seed(tmp_path)
    first = client.post(f"/api/v1/compras/pedidos/{order_id}/recepciones", json={}).json()["recepcion"]
    line = {**first["lineas"][0], "received_quantity": 6, "received_price": 2.2, "lot": "L-1", "expiry": "2026-12-31", "location": "Cámara"}
    saved = client.patch(f"/api/v1/compras/recepciones/{first['id']}", json={"referencia": "ALB-1", "lineas": [line]}).json()["recepcion"]
    assert any(issue["code"] == "DIFERENCIA_CANTIDAD" for issue in saved["incidencias"])
    confirmed = client.post(f"/api/v1/compras/recepciones/{first['id']}/confirmar", json={"confirmacion": "CONFIRMAR_RECEPCION"})
    assert confirmed.status_code == 200 and confirmed.json()["pedido"]["estado"] == "parcialmente_recibido"
    movement = confirmed.json()["movimientos"][0]
    assert movement["cantidad"] == 6 and movement["trazabilidad"]["reception_id"] == first["id"]
    assert movement["trazabilidad"] | {"lot": "L-1", "expiry": "2026-12-31", "location": "Cámara"} == movement["trazabilidad"]
    count = len(json.loads((tmp_path / "DATOS/db/stock_movimientos.json").read_text(encoding="utf-8")))
    repeated = client.post(f"/api/v1/compras/recepciones/{first['id']}/confirmar", json={"confirmacion": "CONFIRMAR_RECEPCION"})
    assert repeated.json()["idempotente"] is True
    assert repeated.json()["stock_modificado"] is False
    assert len(json.loads((tmp_path / "DATOS/db/stock_movimientos.json").read_text(encoding="utf-8"))) == count
    second = client.post(f"/api/v1/compras/pedidos/{order_id}/recepciones", json={}).json()["recepcion"]
    assert second["lineas"][0]["previously_received"] == 6 and second["lineas"][0]["pending_quantity"] == 4
    done = client.post(f"/api/v1/compras/recepciones/{second['id']}/confirmar", json={"confirmacion": "CONFIRMAR_RECEPCION"})
    assert done.json()["pedido"]["estado"] == "recibido"
    assert sum(item["cantidad"] for item in json.loads((tmp_path / "DATOS/db/stock_movimientos.json").read_text(encoding="utf-8"))) == 10


def test_recepcion_realista_010_mas_015_cierra_solo_al_completar(tmp_path: Path) -> None:
    client, order_id = _seed(tmp_path)
    first = client.post(f"/api/v1/compras/pedidos/{order_id}/recepciones", json={}).json()["recepcion"]
    first_line = {**first["lineas"][0], "ordered_quantity": 0.25, "pending_quantity": 0.25, "received_quantity": 0.10}
    # El pedido temporal reproduce exactamente 0,25 kg sin tocar datos reales.
    orders_path = tmp_path / "DATOS/db/compras_pedidos.json"
    orders = json.loads(orders_path.read_text(encoding="utf-8"))
    orders[0]["lineas"][0]["cantidad"] = 0.25
    orders_path.write_text(json.dumps(orders), encoding="utf-8")
    # Reabrir la API hace que MotorCompras lea la cantidad contractual actualizada del fixture.
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))
    client.patch(f"/api/v1/compras/recepciones/{first['id']}", json={"lineas": [first_line]})
    result1 = client.post(f"/api/v1/compras/recepciones/{first['id']}/confirmar", json={"confirmacion": "CONFIRMAR_RECEPCION"}).json()
    assert result1["pedido"]["estado"] == "parcialmente_recibido"
    assert result1["movimientos"][0]["cantidad"] == 0.10
    second = client.post(f"/api/v1/compras/pedidos/{order_id}/recepciones", json={}).json()["recepcion"]
    assert second["lineas"][0]["previously_received"] == 0.10
    assert second["lineas"][0]["pending_quantity"] == 0.15
    assert second["lineas"][0]["received_quantity"] == 0.15
    result2 = client.post(f"/api/v1/compras/recepciones/{second['id']}/confirmar", json={"confirmacion": "CONFIRMAR_RECEPCION"}).json()
    assert result2["pedido"]["estado"] == "recibido"
    quantities = [item["cantidad"] for item in json.loads((tmp_path / "DATOS/db/stock_movimientos.json").read_text(encoding="utf-8"))]
    assert quantities == [0.10, 0.15]
    repeated = client.post(f"/api/v1/compras/recepciones/{second['id']}/confirmar", json={"confirmacion": "CONFIRMAR_RECEPCION"}).json()
    assert repeated["idempotente"] is True
    assert [item["cantidad"] for item in json.loads((tmp_path / "DATOS/db/stock_movimientos.json").read_text(encoding="utf-8"))] == quantities


def test_pedido_multilinea_sigue_parcial_si_una_linea_tiene_pendiente(tmp_path: Path) -> None:
    _write(tmp_path / "DATOS/db/articulos.json", [
        {"codigo": "ART-A", "nombre": "A", "unidad": "kg"},
        {"codigo": "ART-B", "nombre": "B", "unidad": "kg"},
    ])
    motor = MotorCompras(BaseDatosLocal(tmp_path)); motor.crear_proveedor_manual("Proveedor A")
    order = motor.crear_pedidos_borrador_transaccional([{"proveedor": "Proveedor A", "lineas": [
        {"nombre": "A", "articulo_id": "ART-A", "cantidad": 10, "unidad": "kg"},
        {"nombre": "B", "articulo_id": "ART-B", "cantidad": 5, "unidad": "kg"},
    ]}])[0]
    motor.confirmar_borrador_pedido(order["id"], usuario="test")
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))
    reception = client.post(f"/api/v1/compras/pedidos/{order['id']}/recepciones", json={}).json()["recepcion"]
    lines = [{**line, "received_quantity": 10 if line["article_id"] == "ART-A" else 2} for line in reception["lineas"]]
    client.patch(f"/api/v1/compras/recepciones/{reception['id']}", json={"lineas": lines})
    confirmed = client.post(f"/api/v1/compras/recepciones/{reception['id']}/confirmar", json={"confirmacion": "CONFIRMAR_RECEPCION"}).json()
    assert confirmed["pedido"]["estado"] == "parcialmente_recibido"
    next_reception = client.post(f"/api/v1/compras/pedidos/{order['id']}/recepciones", json={}).json()["recepcion"]
    assert len(next_reception["lineas"]) == 1
    assert next_reception["lineas"][0]["article_id"] == "ART-B"
    assert next_reception["lineas"][0]["previously_received"] == 2
    assert next_reception["lineas"][0]["pending_quantity"] == 3


def test_cantidad_distinta_registra_exactamente_y_no_actualiza_precio_maestro(tmp_path: Path) -> None:
    client, order_id = _seed(tmp_path)
    reception = client.post(f"/api/v1/compras/pedidos/{order_id}/recepciones", json={}).json()["recepcion"]
    line = {**reception["lineas"][0], "received_quantity": 9.8, "received_price": 3.5}
    client.patch(f"/api/v1/compras/recepciones/{reception['id']}", json={"lineas": [line]})
    result = client.post(f"/api/v1/compras/recepciones/{reception['id']}/confirmar", json={"confirmacion": "CONFIRMAR_RECEPCION"}).json()
    assert result["movimientos"][0]["cantidad"] == 9.8
    assert json.loads((tmp_path / "DATOS/db/articulos.json").read_text(encoding="utf-8"))[0]["precio"] == 2


def test_unidad_incompatible_y_articulo_sin_relacionar_bloquean(tmp_path: Path) -> None:
    for suffix, unit, code in (("unit", "l", "UNIDAD_INCOMPATIBLE"), ("article", "kg", "ARTICULO_SIN_RELACIONAR")):
        base = tmp_path / suffix; client, order_id = _seed(base, unit=unit)
        reception = client.post(f"/api/v1/compras/pedidos/{order_id}/recepciones", json={}).json()["recepcion"]
        if suffix == "article":
            line = {**reception["lineas"][0], "article_id": ""}
            reception = client.patch(f"/api/v1/compras/recepciones/{reception['id']}", json={"lineas": [line]}).json()["recepcion"]
        assert any(issue["code"] == code for issue in reception["incidencias"])
        response = client.post(f"/api/v1/compras/recepciones/{reception['id']}/confirmar", json={"confirmacion": "CONFIRMAR_RECEPCION"})
        assert response.status_code == 400
        assert json.loads((base / "DATOS/db/stock_movimientos.json").read_text(encoding="utf-8")) == []


def test_unidad_canonicamente_convertible_se_registra_en_unidad_base(tmp_path: Path) -> None:
    client, order_id = _seed(tmp_path, unit="g")
    reception = client.post(f"/api/v1/compras/pedidos/{order_id}/recepciones", json={}).json()["recepcion"]
    assert reception["confirmable"] is True
    result = client.post(
        f"/api/v1/compras/recepciones/{reception['id']}/confirmar",
        json={"confirmacion": "CONFIRMAR_RECEPCION"},
    ).json()
    movement = result["movimientos"][0]
    assert movement["cantidad"] == 0.01
    assert movement["unidad"] == "kg"
    assert movement["trazabilidad"]["quantity_received"] == 10
    assert movement["trazabilidad"]["unit_received"] == "g"
