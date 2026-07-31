from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from SERVICIOS.menu_necesidades_service import MenuNecesidadesService
from SERVICIOS.menus_inteligentes_service import MenusInteligentesService


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


def test_conversion_incompatible_no_inventa_faltante(tmp_path: Path) -> None:
    menu_id = _seed(tmp_path, recipe_unit="u", stock_unit="kg")
    line = MenuNecesidadesService(tmp_path).necesidades(menu_id)["necesidades"]["lines"][0]

    assert line["estado"] == "Conversión pendiente"
    assert line["stock_disponible"] is None
    assert line["cantidad_faltante"] is None


def test_api_genera_propuesta_revisable_sin_modificar_stock_ni_crear_pedido(tmp_path: Path) -> None:
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
    assert body["estado"] == "BORRADOR"
    assert body["grupos_proveedor"][0]["proveedor"] == "Proveedor A"
    assert body["crea_pedido"] is False
    assert body["modifica_stock"] is False
    assert stock_path.read_bytes() == before_stock
    assert not (tmp_path / "DATOS/db/compras_pedidos.json").exists()

    fetched = client.get(f"/api/v1/menus/{menu_id}/propuesta-compra/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["propuesta"]["id"] == body["id"]
