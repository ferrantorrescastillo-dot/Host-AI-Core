from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _client(base: Path) -> TestClient:
    _write(base / "DATOS/db/articulos.json", [{"codigo": "ART-PATATA", "nombre": "Patata Monalisa", "familia": "Verduras", "precio": 2, "activo": True}])
    _write(base / "DATOS/db/compras_proveedores.json", [{"id": "PROV-1", "nombre": "Huerta Sur", "estado": "activo"}])
    for name in ("stock_lotes", "stock_movimientos", "compras_producto_proveedor"):
        _write(base / f"DATOS/db/{name}.json", [])
    _write(base / "DATOS/facturas/historico_precios.json", {"version": "3.0.3.5.3", "registros": []})
    return TestClient(create_app(HostAIPlatformAPI(base_dir=base)))


def _update(**extra: object) -> dict[str, object]:
    return {"confirmacion": "ACTUALIZAR_ARTICULO_MAESTRO", "nombre": "Patata Monalisa", "familia": "Verduras", "unidad_base": "kg", "unidad_compra": "saco", "cantidad_formato": 10, "proveedor_preferente": "Huerta Sur", "precio": 2.5, "referencia_proveedor": "PAT-10", "marca": "Huerta", "conservacion": "Lugar fresco", "alergenos": [], "observaciones": "Ficha confirmada", **extra}


def test_edita_y_persiste_ficha_maestra_sin_duplicar(tmp_path: Path) -> None:
    client = _client(tmp_path)
    response = client.patch("/api/v1/articulos/ART-PATATA", json=_update())
    assert response.status_code == 200
    item = response.json()["articulo"]
    assert item["id"] == "ART-PATATA" and item["unidad_base"] == "kg"
    assert item["unidad_compra"] == "saco" and item["cantidad_formato"] == 10
    assert item["proveedor"] == "Huerta Sur" and item["precio"] == 2.5
    assert item["operatividad"] == {"stock": True, "compras": True, "escandallos": True}
    reloaded = _client_from_existing(tmp_path).get("/api/v1/articulos/ART-PATATA").json()["articulo"]
    assert reloaded["unidad_base"] == "kg" and reloaded["referencia_proveedor"] == "PAT-10"
    assert len(json.loads((tmp_path / "DATOS/db/articulos.json").read_text(encoding="utf-8"))) == 1


def test_valida_unidad_proveedor_precio_y_articulo_incompleto(tmp_path: Path) -> None:
    client = _client(tmp_path)
    for changes, code in [({"unidad_base": "saco"}, "invalid_base_unit"), ({"proveedor_preferente": "Inventado"}, "provider_not_found"), ({"precio": -1}, "invalid_price")]:
        payload = client.patch("/api/v1/articulos/ART-PATATA", json=_update(**changes)).json()
        assert payload["error"]["code"] == code
    detail = client.get("/api/v1/articulos/ART-PATATA").json()["articulo"]
    assert detail["unidad_base"] == "kg"
    assert detail["unidad_base_sugerida"] is True
    assert detail["estado_unidad_base"] == "SUGERIDA_PENDIENTE_REVISION"
    assert detail["operatividad"]["stock"] is True


def test_unidad_sugerida_respeta_existentes_y_se_confirma_al_editar(tmp_path: Path) -> None:
    client = _client(tmp_path)
    suggested = client.get("/api/v1/articulos/ART-PATATA").json()["articulo"]
    assert suggested["unidad_base"] == "kg" and suggested["unidad_base_sugerida"] is True
    changed = client.patch("/api/v1/articulos/ART-PATATA", json=_update(unidad_base="l")).json()["articulo"]
    assert changed["unidad_base"] == "l" and changed["unidad_base_sugerida"] is False
    assert changed["conversion_unidades"] is None

    stored = json.loads((tmp_path / "DATOS/db/articulos.json").read_text(encoding="utf-8"))[0]
    assert stored["unidad"] == "l"
    stored["unidad"] = "kg"; stored["catalogo_maestro"]["unidad_base"] = "kg"
    _write(tmp_path / "DATOS/db/articulos.json", [stored])
    existing = _client_from_existing(tmp_path).get("/api/v1/articulos/ART-PATATA").json()["articulo"]
    assert existing["unidad_base"] == "kg" and existing["unidad_base_sugerida"] is False


def test_stock_acepta_kg_sugerido_sin_crear_conversion(tmp_path: Path) -> None:
    client = _client(tmp_path)
    movement = client.post("/api/v1/stock/movimientos", json={"article_id": "ART-PATATA", "tipo": "INVENTARIO_INICIAL", "cantidad": 2, "unidad": "kg", "confirmacion": "REGISTRAR_MOVIMIENTO_STOCK"})
    assert movement.status_code == 201 and movement.json()["stock_actual"] == 2
    article = client.get("/api/v1/articulos/ART-PATATA").json()["articulo"]
    assert article["unidad_base_sugerida"] is True and article["conversion_unidades"] is None


def test_articulo_nuevo_sin_unidad_persiste_kg_sugerido(tmp_path: Path) -> None:
    repository = RepositorioProductosMaestro601(tmp_path)
    created = repository.crear_producto({"codigo": "ART-NUEVO", "nombre": "Producto importado"})
    assert created["unidad_base"] == "kg" and created["unidad_base_sugerida"] is True
    raw = json.loads((tmp_path / "DATOS/db/articulos.json").read_text(encoding="utf-8"))[0]
    assert raw["unidad"] == "kg"
    assert raw["catalogo_maestro"]["unidad_base_sugerida"] is True


def test_unidad_base_integra_stock_y_no_rompe_compras(tmp_path: Path) -> None:
    client = _client(tmp_path)
    assert client.patch("/api/v1/articulos/ART-PATATA", json=_update()).status_code == 200
    api = HostAIPlatformAPI(base_dir=tmp_path)
    client = TestClient(create_app(api))
    movement = client.post("/api/v1/stock/movimientos", json={"article_id": "ART-PATATA", "tipo": "INVENTARIO_INICIAL", "cantidad": .5, "unidad": "kg", "confirmacion": "REGISTRAR_MOVIMIENTO_STOCK"}).json()
    assert movement["stock_actual"] == .5
    need = api.facade._get_core().stock.predecir_necesidad("Patata Monalisa", .75, "kg", "ART-PATATA")
    assert need["cantidad_faltante"] == .25
    assert api.facade._get_core().compras.listar_proveedores(incluir_inactivos=False)[0]["nombre"] == "Huerta Sur"


def _client_from_existing(base: Path) -> TestClient:
    return TestClient(create_app(HostAIPlatformAPI(base_dir=base)))
