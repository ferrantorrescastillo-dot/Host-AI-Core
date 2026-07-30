from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from API.http_server import create_app
from API.app import HostAIPlatformAPI
from SERVICIOS.articulos_catalog_read_service import ArticulosCatalogReadService


def _fixture(base: Path) -> None:
    db = base / "DATOS" / "db"
    invoices = base / "DATOS" / "facturas"
    db.mkdir(parents=True)
    invoices.mkdir(parents=True)
    (db / "articulos.json").write_text(json.dumps([
        {"codigo": "ART-001", "nombre": "Tomate pera", "familia": "Verduras", "proveedor": "Huerta Sur", "precio": 2.5, "unidad": "kg", "activo": True}
    ]), encoding="utf-8")
    (db / "proveedores.json").write_text("[]", encoding="utf-8")
    (db / "compras_producto_proveedor.json").write_text(json.dumps([
        {"producto": "Tomate pera", "proveedor": "Huerta Sur", "precio": 2.5, "unidad": "kg", "preferente": True}
    ]), encoding="utf-8")
    (invoices / "historico_precios.json").write_text(json.dumps({"registros": [
        {"articulo_id": "ART-001", "nombre_articulo": "Tomate pera", "precio": 2.5, "unidad": "kg", "proveedor_nombre": "Huerta Sur", "fecha_factura": "2026-07-01"}
    ]}), encoding="utf-8")


class _Stock:
    def stock_actual(self):
        return {"items": [{"articulo_id": "ART-001", "nombre": "Tomate pera", "cantidad": 8, "unidad": "kg", "lotes": [{"id": "L-1"}]}]}


def test_catalogo_busca_filtra_pagina_y_detalla_datos_reales(tmp_path: Path) -> None:
    _fixture(tmp_path)
    service = ArticulosCatalogReadService(tmp_path, stock=_Stock())
    listed = service.listar({"q": "tomate", "familia": "Verduras", "page": "1", "page_size": "10"})
    assert listed["catalogo"]["total"] == 1
    assert listed["catalogo"]["items"][0]["stock"] == 8
    detail = service.obtener("ART-001")
    assert detail["articulo"]["proveedores"][0]["nombre"] == "Huerta Sur"
    assert detail["articulo"]["precios"][0]["precio"] == 2.5
    assert detail["articulo"]["documentos"] == []
    assert detail["articulo"]["recetas"] == []


def test_catalogo_sin_datos_y_error_controlado(tmp_path: Path) -> None:
    service = ArticulosCatalogReadService(tmp_path)
    assert service.listar({})["catalogo"]["items"] == []
    invalid = service.listar({"desconocido": "x"})
    assert invalid["ok"] is False
    assert invalid["error"]["status"] == 400
    missing = service.obtener("NO-EXISTE")
    assert missing["error"]["status"] == 404


def test_http_catalogo_lista_detalle_y_no_modifica_datos(tmp_path: Path) -> None:
    _fixture(tmp_path)
    client = TestClient(create_app(HostAIPlatformAPI(base_dir=tmp_path)))
    before = (tmp_path / "DATOS" / "db" / "articulos.json").read_bytes()
    response = client.get("/api/v1/articulos?q=tomate")
    assert response.status_code == 200
    assert response.json()["catalogo"]["total"] == 1
    detail = client.get("/api/v1/articulos/ART-001")
    assert detail.status_code == 200
    assert detail.json()["articulo"]["codigo"] == "ART-001"
    assert client.get("/api/v1/articulos/NO-EXISTE").status_code == 404
    assert (tmp_path / "DATOS" / "db" / "articulos.json").read_bytes() == before
