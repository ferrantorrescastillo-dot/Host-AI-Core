from __future__ import annotations

import json
from pathlib import Path

import pytest

from SERVICIOS.catalog_crud_write_service import CatalogCrudError, CatalogCrudWriteService
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext


def context(*scopes: str) -> AuthorizedExecutionContext:
    return AuthorizedExecutionContext(request_id="REQ-CRUD-1", user_id="USR-1", tenant_id="TEN-1", roles=("chef",), scopes=frozenset(scopes))


def seed(base: Path) -> None:
    db = base / "DATOS" / "db"; db.mkdir(parents=True)
    (db / "eventos.json").write_text("[]", encoding="utf-8")
    (db / "articulos.json").write_text("[]", encoding="utf-8")


def test_event_preview_confirm_and_idempotency(tmp_path: Path) -> None:
    seed(tmp_path); service = CatalogCrudWriteService(tmp_path)
    preview = service.preview(domain="EVENTO", operation="CREAR", entity_id="", session_id="S1", context=context("eventos:preview"), payload={"nombre": "Boda segura", "fecha": "2030-05-20", "pax": 40})
    assert preview["datos_reales_modificados"] is False
    assert json.loads((tmp_path / "DATOS/db/eventos.json").read_text()) == []
    result = service.confirm(preview_token=preview["preview_token"], session_id="S1", context=context("eventos:write"))
    repeated = service.confirm(preview_token=preview["preview_token"], session_id="S1", context=context("eventos:write"))
    assert result["registro"]["id"].startswith("EVT_")
    assert repeated["idempotente"] is True
    assert len(json.loads((tmp_path / "DATOS/db/eventos.json").read_text())) == 1


def test_article_create_does_not_touch_stock_and_rejects_duplicate(tmp_path: Path) -> None:
    seed(tmp_path); stock = tmp_path / "DATOS/db/stock_movimientos.json"; stock.write_text("[]", encoding="utf-8")
    service = CatalogCrudWriteService(tmp_path)
    preview = service.preview(domain="ARTICULO", operation="CREAR", entity_id="", session_id="S1", context=context("articulos:preview"), payload={"nombre": "Azúcar", "codigo": "ART-AZUCAR", "unidad_base": "kg"})
    service.confirm(preview_token=preview["preview_token"], session_id="S1", context=context("articulos:write"))
    assert json.loads(stock.read_text()) == []
    with pytest.raises(CatalogCrudError, match="nombre"):
        service.preview(domain="ARTICULO", operation="CREAR", entity_id="", session_id="S1", context=context("articulos:preview"), payload={"nombre": "azúcar", "codigo": "OTRO"})


def test_recipe_create_update_archive_and_cancelled_preview(tmp_path: Path) -> None:
    seed(tmp_path)
    (tmp_path / "DATOS/db/articulos.json").write_text(json.dumps([{"id": "ART-SAL", "codigo": "ART-SAL", "nombre": "Sal"}]), encoding="utf-8")
    service = CatalogCrudWriteService(tmp_path)
    payload = {"nombre": "Salsa prueba", "codigo": "SALSA-PRUEBA", "numero_raciones": 4, "ingredientes": ["sal"], "cantidades": ["4 g"], "ingredientes_estructurados": [{"nombre": "sal", "article_id": "ART-SAL", "estado": "RESUELTO"}], "elaboracion": "Mezclar."}
    preview = service.preview(domain="RECETA", operation="CREAR", entity_id="", session_id="S1", context=context("recetas:preview"), payload=payload)
    before = json.loads((tmp_path / "DATOS/db/biblioteca_recetas_601.json").read_text(encoding="utf-8"))
    assert before["recetas"] == []
    created = service.confirm(preview_token=preview["preview_token"], session_id="S1", context=context("recetas:write"))["registro"]
    assert created["ingredientes_estructurados"][0]["article_id"] == "ART-SAL"
    update = service.preview(domain="RECETA", operation="MODIFICAR", entity_id=created["id"], session_id="S1", context=context("recetas:preview"), payload={"observaciones": "Actualizada"})
    updated = service.confirm(preview_token=update["preview_token"], session_id="S1", context=context("recetas:write"))["registro"]
    assert updated["observaciones"] == "Actualizada"
    archive = service.preview(domain="RECETA", operation="ARCHIVAR", entity_id=created["id"], session_id="S1", context=context("recetas:preview"), payload={})
    service.confirm(preview_token=archive["preview_token"], session_id="S1", context=context("recetas:write"))
    assert service.recipes.obtener(created["id"])["estado"] == "ARCHIVADA"
    with pytest.raises(CatalogCrudError, match="ya está archivada"):
        service.preview(domain="RECETA", operation="ARCHIVAR", entity_id=created["id"], session_id="S1", context=context("recetas:preview"), payload={})
