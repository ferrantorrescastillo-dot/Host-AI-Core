import json

import pytest

from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.precio_referencia_web_service import PrecioReferenciaWebService
from SERVICIOS.precio_referencias_import_service import PrecioReferenciasImportService


def context():
    return AuthorizedExecutionContext("REQ", "CHEF", "LOCAL", ("chef",), frozenset({"articulos:write"}))


def setup_service(tmp_path, count=2):
    db = tmp_path / "DATOS" / "db"; db.mkdir(parents=True)
    articles = [{"codigo": f"ART-{index}", "nombre": f"Artículo {index}", "unidad_base": "kg", "unidad_compra": "bandeja", "cantidad_formato": 500, "unidad_formato": "g", "precio": None, "proveedor": "Proveedor real"} for index in range(1, count + 1)]
    (db / "articulos.json").write_text(json.dumps(articles), encoding="utf-8")
    recipes = [{"codigo": f"REC-{index}", "ingredientes": [{"articulo_id": f"ART-{((index - 1) % count) + 1}"} for _ in range(4)]} for index in range(1, 21)]
    (db / "biblioteca_recetas_601.json").write_text(json.dumps(recipes), encoding="utf-8")
    return PrecioReferenciasImportService(tmp_path, PrecioReferenciaWebService(tmp_path)), db


def test_missing_articles_are_consolidated_by_canonical_article_id(tmp_path) -> None:
    service, _ = setup_service(tmp_path, 12)
    result = service.missing_articles()
    assert result["total"] == 12
    assert len({item["article_id"] for item in result["articulos"]}) == 12
    assert sum(item["usado_en_recetas"] for item in result["articulos"]) == 20
    exported = service.export_text()
    assert exported["total"] == 12 and exported["coste_ia_usd"] == "0.00000000"
    assert "proveedor_referencia" in exported["texto"]
    assert "no es el proveedor real" in exported["texto"]


@pytest.mark.parametrize("payload, detected", [
    ('[{"article_id":"ART-1","artículo":"Champiñones","producto":"Champiñón","tienda":"Makro","formato":"500 g","precio":"2.50","moneda":"EUR","url":"https://example.test/champ"}]', "JSON"),
    ("article_id,artículo,producto,tienda,formato,precio,moneda,url\nART-1,Champiñones,Champiñón,Makro,500 g,2.50,EUR,https://example.test/champ", "CSV"),
    ("article_id\tartículo\tproducto\ttienda\tformato\tprecio\tmoneda\turl\nART-1\tChampiñones\tChampiñón\tMakro\t500 g\t2.50\tEUR\thttps://example.test/champ", "TSV"),
    ("| article_id | artículo | producto | tienda | formato | precio | moneda | url |\n|---|---|---|---|---|---|---|---|\n| ART-1 | Champiñones | Champiñón | Makro | 500 g | 2.50 | EUR | https://example.test/champ |", "MARKDOWN"),
])
def test_deterministic_formats_preview_without_writing(tmp_path, payload, detected) -> None:
    service, db = setup_service(tmp_path)
    before = (db / "articulos.json").read_text(encoding="utf-8")
    preview = service.preview(payload, context())
    assert preview["formato_detectado"] == detected and preview["resumen"] == {"listas": 1, "ambiguas": 0, "invalidas": 0}
    assert preview["listas"][0]["referencia"]["precio_normalizado"] == 5
    assert preview["listas"][0]["referencia"]["origen"] == "IMPORTADO"
    assert (db / "articulos.json").read_text(encoding="utf-8") == before


def test_bulk_confirm_preserves_real_price_and_provider_and_is_idempotent(tmp_path) -> None:
    service, db = setup_service(tmp_path)
    raw = "article_id,artículo,producto,tienda,formato,precio,moneda,url\nART-1,Champiñones,Champiñón,Makro,500 g,2.50,EUR,https://example.test/champ\nART-2,Cava,Cava,Carrefour,750 ml,3.00,EUR,https://example.test/cava"
    preview = service.preview(raw, context())
    confirmed = service.confirm(preview["listas"], context())
    repeated = service.confirm(preview["listas"], context())
    values = json.loads((db / "articulos.json").read_text(encoding="utf-8"))
    assert confirmed["confirmadas"] == 2 and repeated["confirmadas"] == 2
    assert values[0]["precio"] is None and values[0]["proveedor"] == "Proveedor real"
    assert len(values[0]["precios_referencia"]) == 1
    assert values[0]["precios_referencia"][0]["tienda_referencia"] == "Makro"
    assert preview["precio_real_modificado"] is False
    assert preview["proveedor_real_modificado"] is False
    assert confirmed["precio_real_modificado"] is False
    assert confirmed["proveedor_real_modificado"] is False


def test_proveedor_referencia_alias_never_replaces_real_supplier(tmp_path) -> None:
    service, db = setup_service(tmp_path, 1)
    raw = "article_id,artículo,producto,proveedor_referencia,formato,precio,moneda,url\nART-1,Artículo 1,Producto externo,Proveedor externo,500 g,2.50,EUR,https://example.test/producto"
    preview = service.preview(raw, context())
    assert preview["listas"][0]["proveedor_real_actual"] == "Proveedor real"
    assert preview["listas"][0]["referencia"]["tienda_referencia"] == "Proveedor externo"

    service.confirm(preview["listas"], context())
    stored = json.loads((db / "articulos.json").read_text(encoding="utf-8"))[0]
    assert stored["precio"] is None
    assert stored["proveedor"] == "Proveedor real"
    assert stored["precios_referencia"][0]["tienda_referencia"] == "Proveedor externo"


def test_imported_reference_is_idempotent_after_service_restart(tmp_path) -> None:
    service, db = setup_service(tmp_path, 1)
    raw = "article_id,artículo,producto,proveedor_referencia,formato,precio,moneda,url\nART-1,Artículo 1,Producto externo,Proveedor externo,500 g,2.50,EUR,https://example.test/producto"
    first_preview = service.preview(raw, context())
    first = service.confirm(first_preview["listas"], context())
    assert first["datos_reales_modificados"] is True

    restarted = PrecioReferenciasImportService(tmp_path, PrecioReferenciaWebService(tmp_path))
    restored_preview = restarted.active(context())
    assert restored_preview["workflow"]["estado"] == "CONFIRMADO"
    assert restored_preview["workflow"]["preview"]["listas"][0]["article_id"] == "ART-1"
    replay = restarted.confirm(first_preview["listas"], context())
    assert replay["datos_reales_modificados"] is False
    assert replay["resultados"][0]["idempotente"] is True

    fresh_preview = restarted.preview(raw, context())
    rerun = restarted.confirm(fresh_preview["listas"], context())
    assert rerun["datos_reales_modificados"] is False
    stored = json.loads((db / "articulos.json").read_text(encoding="utf-8"))[0]
    assert len(stored["precios_referencia"]) == 1
    audit = (tmp_path / "DATOS/auditoria/precios_referencia_web.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(audit) == 1

    restarted.discard(context())
    assert PrecioReferenciasImportService(tmp_path, PrecioReferenciaWebService(tmp_path)).active(context())["workflow"] is None
