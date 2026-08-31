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
