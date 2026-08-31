from pathlib import Path

import pytest

from CORE.host_ai_core import HostAICore
from SERVICIOS.biblioteca_escandallos_601 import BibliotecaEscandallos601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.escandallo_editor_service import EscandalloEditorError, EscandalloEditorService
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.receta_documentacion_write_service import RecetaDocumentacionError, RecetaDocumentacionWriteService
from SERVICIOS.stock_lote_write_service import StockLoteWriteError, StockLoteWriteService


def context(*scopes: str) -> AuthorizedExecutionContext:
    return AuthorizedExecutionContext(request_id="REQ-1", user_id="USR-1", tenant_id="TEN-1", roles=("chef",), scopes=frozenset(scopes))


def test_stock_location_preview_confirm_idempotency_and_quantity_invariant(tmp_path: Path) -> None:
    core = HostAICore(tmp_path)
    existing = core.stock.registrar_entrada("Patata", 2, "kg", ubicacion="Cámara", articulo_id="ART-PAT")["lote"]
    target = core.stock.registrar_entrada("Cebolla", 3, "kg", ubicacion="", articulo_id="ART-CEB")["lote"]
    service = StockLoteWriteService(core)
    assert service.detail(target["id"])["incidencias"][0]["code"] == "SIN_UBICACION"
    preview = service.preview_location(lot_id=target["id"], location_id="Cámara", context=context("stock:write"))
    assert preview["datos_reales_modificados"] is False
    assert core.stock.lotes[target["id"]].cantidad == 3
    confirmed = service.confirm_location(lot_id=target["id"], location_id="Cámara", preview_token=preview["preview_token"], context=context("stock:write"))
    assert confirmed["lote"]["ubicacion"] == "Cámara"
    assert confirmed["lote"]["cantidad"] == 3
    again = service.preview_location(lot_id=target["id"], location_id="Cámara", context=context("stock:write"))
    assert again["estado"] == "SIN_CAMBIOS"
    reloaded = HostAICore(tmp_path)
    assert reloaded.stock.lotes[target["id"]].ubicacion == "Cámara"
    assert existing["id"] in reloaded.stock.lotes


def test_stock_location_rejects_invalid_location_and_lot(tmp_path: Path) -> None:
    core = HostAICore(tmp_path); lot = core.stock.registrar_entrada("Patata", 1, "kg", ubicacion="", articulo_id="A")["lote"]
    service = StockLoteWriteService(core)
    with pytest.raises(StockLoteWriteError, match="canónica"):
        service.preview_location(lot_id=lot["id"], location_id="Texto libre", context=context("stock:write"))
    with pytest.raises(StockLoteWriteError, match="no encontrado"):
        service.detail("LOTE-NO")


def test_stock_location_cancel_invalidates_preview_and_replacement(tmp_path: Path) -> None:
    core = HostAICore(tmp_path)
    core.stock.registrar_entrada("Referencia", 1, "kg", ubicacion="Cámara", articulo_id="REF")
    core.stock.registrar_entrada("Otra referencia", 1, "kg", ubicacion="Bodega", articulo_id="REF-2")
    lot = core.stock.registrar_entrada("Patata", 2, "kg", ubicacion="", articulo_id="PAT")["lote"]
    service = StockLoteWriteService(core)
    first = service.preview_location(lot_id=lot["id"], location_id="Cámara", context=context("stock:preview"), session_id="chat")
    second = service.preview_location(lot_id=lot["id"], location_id="Bodega", context=context("stock:preview"), session_id="chat")
    with pytest.raises(StockLoteWriteError, match="no corresponde"):
        service.confirm_location(lot_id=lot["id"], location_id="Cámara", preview_token=first["preview_token"], context=context("stock:write"), session_id="chat")
    service.discard_location(preview_token=second["preview_token"], context=context("stock:preview"), session_id="chat")
    with pytest.raises(StockLoteWriteError, match="no corresponde"):
        service.confirm_location(lot_id=lot["id"], location_id="Bodega", preview_token=second["preview_token"], context=context("stock:write"), session_id="chat")
    assert core.stock.lotes[lot["id"]].ubicacion == ""


def test_stock_location_expiry_fingerprint_permissions_and_double_confirm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    core = HostAICore(tmp_path)
    core.stock.registrar_entrada("Referencia", 1, "kg", ubicacion="Cámara", articulo_id="REF")
    lot = core.stock.registrar_entrada("Patata", 2, "kg", ubicacion="", articulo_id="PAT")["lote"]
    service = StockLoteWriteService(core)
    with pytest.raises(StockLoteWriteError, match="autorizado"):
        service.preview_location(lot_id=lot["id"], location_id="Cámara", context=context("stock:read"))
    preview = service.preview_location(lot_id=lot["id"], location_id="Cámara", context=context("stock:preview"))
    core.stock.lotes[lot["id"]].cantidad = 3
    with pytest.raises(StockLoteWriteError, match="ha cambiado"):
        service.confirm_location(lot_id=lot["id"], location_id="Cámara", preview_token=preview["preview_token"], context=context("stock:write"))
    preview = service.preview_location(lot_id=lot["id"], location_id="Cámara", context=context("stock:preview"))
    confirmed = service.confirm_location(lot_id=lot["id"], location_id="Cámara", preview_token=preview["preview_token"], context=context("stock:write"))
    repeated = service.confirm_location(lot_id=lot["id"], location_id="Cámara", preview_token=preview["preview_token"], context=context("stock:write"))
    assert confirmed == repeated and repeated["lote"]["cantidad"] == 3
    core.stock.registrar_entrada("Otra", 1, "kg", ubicacion="Bodega", articulo_id="OTHER")
    expiring = service.preview_location(lot_id=lot["id"], location_id="Bodega", context=context("stock:preview"))
    monkeypatch.setattr("SERVICIOS.stock_lote_write_service.time.monotonic", lambda: float("inf"))
    with pytest.raises(StockLoteWriteError, match="caducado"):
        service.confirm_location(lot_id=lot["id"], location_id="Bodega", preview_token=expiring["preview_token"], context=context("stock:write"))


def _costing(tmp_path: Path) -> tuple[EscandalloEditorService, str, str]:
    library = BibliotecaEscandallos601(tmp_path)
    code = str(library.repo_prod.crear_producto({"nombre": "Harina", "familia": "TEST", "unidad_base": "kg", "unidad_compra": "kg", "precio": 2, "proveedor": "P"})["codigo"])
    created = library.crear_manual({"nombre": "Masa", "numero_raciones": 10, "lineas": [{"producto_codigo": code, "nombre_mostrado": "Harina", "cantidad_neta": 1, "unidad_receta": "kg"}]})["escandallo"]
    return EscandalloEditorService(tmp_path, library), str(created["id"]), code


def test_costing_editor_preview_confirm_add_remove_and_canonical_recalculation(tmp_path: Path) -> None:
    service, esc_id, article = _costing(tmp_path)
    changes = {"numero_raciones": 5, "lineas": [{"producto_codigo": article, "nombre_mostrado": "Harina", "cantidad_neta": 2, "unidad_receta": "kg"}]}
    preview = service.preview(escandallo_id=esc_id, changes=changes, context=context("escandallos:write"))
    assert preview["escandallo_propuesto"]["coste_total"] == pytest.approx(4)
    assert service.library.repo_esc.obtener(esc_id)["numero_raciones"] == 10
    result = service.confirm(escandallo_id=esc_id, changes=changes, preview_token=preview["preview_token"], context=context("escandallos:write"))
    assert result["escandallo"]["coste_por_racion"] == pytest.approx(.8)
    assert len(result["escandallo"]["lineas"]) == 1


@pytest.mark.parametrize("changes,code", [
    ({"numero_raciones": 5, "lineas": [{"producto_codigo": "NO", "cantidad_neta": 1, "unidad_receta": "kg"}]}, "article_not_found"),
    ({"numero_raciones": 5, "lineas": [{"producto_codigo": "ARTICLE", "cantidad_neta": 0, "unidad_receta": "kg"}]}, "invalid_quantity"),
])
def test_costing_editor_blocks_invalid_data(tmp_path: Path, changes: dict, code: str) -> None:
    service, esc_id, article = _costing(tmp_path)
    changes["lineas"][0]["producto_codigo"] = article if changes["lineas"][0]["producto_codigo"] == "ARTICLE" else "NO"
    with pytest.raises(EscandalloEditorError) as error: service.preview(escandallo_id=esc_id, changes=changes, context=context("escandallos:write"))
    assert error.value.code == code


def _recipe(tmp_path: Path) -> tuple[RecetaDocumentacionWriteService, str]:
    repo = RepositorioBibliotecaRecetas601(tmp_path)
    result = repo.crear({"nombre": "Crema", "codigo": "REC-CREMA", "tipo": "Elaboración", "ingredientes": ["Leche"], "cantidades": ["1 l"], "numero_raciones": 4, "elaboracion": "Existente"})
    return RecetaDocumentacionWriteService(tmp_path, repo), str(result["receta"]["id"])


def test_recipe_documentation_structured_partial_preview_confirm_and_allergens(tmp_path: Path) -> None:
    service, recipe_id = _recipe(tmp_path)
    proposal = service.proposal(recipe_id=recipe_id, proposed={"descripcion": "Suave", "tiempo_total": "30 min", "alergenos": ["Lácteos"]}, detected_allergens=["Lácteos"])
    assert proposal["alergenos_detectados_datos"] == ["Lácteos"]
    assert proposal["alergenos_propuestos_ia"] == ["Lácteos"]
    selected = {"descripcion": "Crema suave"}
    preview = service.preview(recipe_id=recipe_id, selected=selected, overwrite_fields=[], context=context("recetas:write"))
    assert service.repository.obtener(recipe_id).get("descripcion") in (None, "")
    confirmed = service.confirm(recipe_id=recipe_id, selected=selected, overwrite_fields=[], preview_token=preview["preview_token"], context=context("recetas:write"))
    assert confirmed["campos_confirmados"] == ["descripcion"]
    assert not service.repository.obtener(recipe_id).get("tiempo_total")


def test_recipe_documentation_does_not_overwrite_without_explicit_selection(tmp_path: Path) -> None:
    service, recipe_id = _recipe(tmp_path)
    with pytest.raises(RecetaDocumentacionError) as error:
        service.preview(recipe_id=recipe_id, selected={"elaboracion": "Propuesta IA"}, overwrite_fields=[], context=context("recetas:write"))
    assert error.value.code == "overwrite_confirmation_required"
    preview = service.preview(recipe_id=recipe_id, selected={"elaboracion": "Editado por usuario"}, overwrite_fields=["elaboracion"], context=context("recetas:write"))
    result = service.confirm(recipe_id=recipe_id, selected={"elaboracion": "Editado por usuario"}, overwrite_fields=["elaboracion"], preview_token=preview["preview_token"], context=context("recetas:write"))
    assert result["receta"]["elaboracion"] == "Editado por usuario"
