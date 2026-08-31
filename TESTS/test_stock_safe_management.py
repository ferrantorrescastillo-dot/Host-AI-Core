from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from CORE.host_ai_core import HostAICore
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601
from SERVICIOS.stock_ajustes_service import StockAjusteError, StockAjustesService
from SERVICIOS.stock_lote_write_service import StockLoteWriteService


def context(*scopes: str) -> AuthorizedExecutionContext:
    return AuthorizedExecutionContext(request_id="REQ-STOCK", user_id="USR-1", tenant_id="TEN-1", roles=("chef",), scopes=frozenset(scopes))


def setup_stock(tmp_path: Path):
    core = HostAICore(tmp_path)
    article = RepositorioProductosMaestro601(tmp_path).crear_producto({"nombre": "Patata", "familia": "VERDURA", "unidad_base": "kg", "unidad_compra": "kg", "precio": 1, "proveedor": "Proveedor"})
    article_id = str(article["codigo"])
    entry = core.stock.registrar_entrada("Patata", 5, "kg", ubicacion="Cámara", articulo_id=article_id, motivo="Entrada inicial")
    return core, article_id, entry["lote"]


def test_adjustment_preview_confirm_is_idempotent_and_traceable(tmp_path: Path) -> None:
    core, article_id, _lot = setup_stock(tmp_path)
    service = StockAjustesService(core)
    preview = service.preview({"article_id": article_id, "cantidad_objetivo": 3, "unidad": "kg", "motivo": "Recuento físico"}, context("stock:preview"))
    assert preview["stock_anterior"] == 5
    assert preview["stock_resultante"] == 3
    assert preview["diferencia"] == -2
    assert preview["datos_reales_modificados"] is False
    assert len(core.stock.movimientos) == 1
    confirmed = service.confirm({"preview_token": preview["preview_token"]}, context("stock:write"))
    repeated = service.confirm({"preview_token": preview["preview_token"]}, context("stock:write"))
    assert confirmed["stock_actual"] == 3
    assert repeated["idempotente"] is True
    assert len(core.stock.movimientos) == 2
    movement = confirmed["movimiento"]
    assert movement["tipo"] == "ajuste_negativo"
    assert movement["observaciones"] == "Recuento físico"


def test_adjustment_cancel_and_stale_preview_never_write(tmp_path: Path) -> None:
    core, article_id, _lot = setup_stock(tmp_path)
    service = StockAjustesService(core)
    preview = service.preview({"article_id": article_id, "cantidad_objetivo": 4, "unidad": "kg", "motivo": "Recuento"}, context("stock:preview"))
    service.discard({"preview_token": preview["preview_token"]}, context("stock:preview"))
    with pytest.raises(StockAjusteError, match="no está disponible"):
        service.confirm({"preview_token": preview["preview_token"]}, context("stock:write"))
    assert len(core.stock.movimientos) == 1

    stale = service.preview({"article_id": article_id, "cantidad_objetivo": 4, "unidad": "kg", "motivo": "Recuento"}, context("stock:preview"))
    core.stock.registrar_entrada("Patata", 1, "kg", articulo_id=article_id, motivo="Entrada concurrente")
    with pytest.raises(StockAjusteError, match="ha cambiado"):
        service.confirm({"preview_token": stale["preview_token"]}, context("stock:write"))


def test_lot_and_locations_are_derived_read_views(tmp_path: Path) -> None:
    core, _article_id, lot = setup_stock(tmp_path)
    service = StockLoteWriteService(core)
    detail = service.detail(str(lot["id"]))
    assert detail["lote"]["id"] == lot["id"]
    assert detail["movimientos"]
    locations = service.locations()["ubicaciones"]
    assert [item["nombre"] for item in locations] == ["Congelador", "Cámara", "Seco", "Bodega", "Limpieza"]
    camera = next(item for item in locations if item["id"] == "Cámara")
    assert camera["total_lotes"] == 1
    assert camera["lotes"][0]["id"] == lot["id"]


def test_location_change_is_canonical_safe_and_preserves_quantity(tmp_path: Path) -> None:
    core, _article_id, lot = setup_stock(tmp_path)
    service = StockLoteWriteService(core)
    before = float(lot["cantidad"])
    preview = service.preview_location(lot_id=lot["id"], location_id="Congelador", context=context("stock:preview"))
    assert preview["datos_reales_modificados"] is False
    confirmed = service.confirm_location(lot_id=lot["id"], location_id="Congelador", preview_token=preview["preview_token"], context=context("stock:write"))
    assert confirmed["lote"]["ubicacion"] == "Congelador"
    assert float(confirmed["lote"]["cantidad"]) == before
    with pytest.raises(Exception, match="canónica"):
        service.preview_location(lot_id=lot["id"], location_id="Habitación inventada", context=context("stock:preview"))


def test_stock_http_usa_actor_interno_canonico_para_ajuste_y_ubicacion(tmp_path: Path, monkeypatch) -> None:
    for name in ("HOST_AI_INTERNAL_USER_ID", "HOST_AI_INTERNAL_TENANT_ID", "HOST_AI_INTERNAL_ROLES", "HOST_AI_INTERNAL_SCOPES"):
        monkeypatch.delenv(name, raising=False)
    platform = HostAIPlatformAPI(base_dir=tmp_path)
    core = platform.facade._get_core()
    article = RepositorioProductosMaestro601(tmp_path).crear_producto({"nombre": "Patata", "familia": "VERDURA", "unidad_base": "kg", "unidad_compra": "kg", "precio": 1, "proveedor": "Proveedor"})
    lot = core.stock.registrar_entrada("Patata", 5, "kg", ubicacion="", articulo_id=str(article["codigo"]), motivo="Entrada inicial")["lote"]
    client = TestClient(create_app(platform))

    adjustment = client.post("/api/v1/stock/ajustes/preview", json={"article_id": article["codigo"], "cantidad_objetivo": 5, "unidad": "kg", "motivo": "Recuento"})
    preview = client.post(f"/api/v1/stock/lotes/{lot['id']}/ubicacion/preview", json={"location_id": "Cámara"})
    confirmed = client.post(f"/api/v1/stock/lotes/{lot['id']}/ubicacion/confirmar", json={"location_id": "Cámara", "preview_token": preview.json()["preview_token"]})

    assert adjustment.status_code == 200
    assert preview.status_code == 200 and preview.json()["datos_reales_modificados"] is False
    assert confirmed.status_code == 200 and confirmed.json()["lote"]["ubicacion"] == "Cámara"
    assert confirmed.json()["lote"]["cantidad"] == 5
