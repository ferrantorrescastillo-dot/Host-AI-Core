from __future__ import annotations
import json
from pathlib import Path
from fastapi.testclient import TestClient
from API.app import HostAIPlatformAPI
from API.http_server import create_app
from SERVICIOS.articulo_documentacion_write_service import ArticuloDocumentacionWriteService
from SERVICIOS.precio_referencia_web_service import PrecioReferenciaWebService

class FakeArticleGenerator:
    def generate(self, **_kwargs): return {"familia": "Verduras", "precio": 99, "stock": 100}

def client(base: Path) -> TestClient: return TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=base)))

def test_event_detail_and_safe_create_http(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "DATOS/db"; db.mkdir(parents=True)
    (db / "eventos.json").write_text(json.dumps([{"id": "EVT-1", "nombre": "Boda", "fecha": "2030-01-01", "pax": 30, "estado": "borrador", "servicios": []}]), encoding="utf-8")
    (db / "articulos.json").write_text("[]", encoding="utf-8")
    http = client(tmp_path)
    assert http.get("/api/v1/eventos/EVT-1").json()["evento"]["nombre"] == "Boda"
    assert http.get("/api/v1/eventos/NO-EXISTE").status_code == 404
    monkeypatch.setenv("HOST_AI_INTERNAL_USER_ID", "USR-HTTP"); monkeypatch.setenv("HOST_AI_INTERNAL_TENANT_ID", "TEN-HTTP")
    monkeypatch.setenv("HOST_AI_INTERNAL_SCOPES", "eventos:preview eventos:write")
    preview = http.post("/api/v1/catalogo/preview", json={"dominio": "EVENTO", "operacion": "CREAR", "payload": {"nombre": "Comida", "fecha": "2030-02-01", "pax": 12}, "session_id": "web"})
    assert preview.status_code == 200 and preview.json()["datos_reales_modificados"] is False
    assert len(json.loads((db / "eventos.json").read_text())) == 1
    confirmed = http.post("/api/v1/catalogo/confirmar", json={"preview_token": preview.json()["preview_token"], "session_id": "web"})
    assert confirmed.status_code == 200 and confirmed.json()["datos_reales_modificados"] is True
    assert len(json.loads((db / "eventos.json").read_text())) == 2


def test_recipe_can_create_and_link_article_through_real_http_without_touching_stock(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "DATOS/db"; db.mkdir(parents=True)
    recipe_id = "REC601-HTTP-1"
    (db / "articulos.json").write_text("[]", encoding="utf-8")
    (db / "biblioteca_recetas_601.json").write_text(json.dumps({
        "version_modelo": "6.0.1",
        "recetas": [{
            "id": recipe_id, "codigo": "REC-HTTP", "nombre": "Masa HTTP",
            "numero_raciones": 4, "ingredientes": ["Harina especial"],
            "cantidades": ["1 kg"], "ingredientes_estructurados": [],
            "elaboracion": "Mezclar.", "estado": "PENDIENTE_DE_COMPLETAR",
        }],
    }), encoding="utf-8")
    stock_lotes = db / "stock_lotes.json"
    stock_movimientos = db / "stock_movimientos.json"
    stock_lotes.write_text('[{"id":"LOTE-1","articulo_id":"OTRO","cantidad":2}]', encoding="utf-8")
    stock_movimientos.write_text('[{"id":"MOV-1","tipo":"ENTRADA"}]', encoding="utf-8")
    stock_before = (stock_lotes.read_bytes(), stock_movimientos.read_bytes())
    for name in (
        "HOST_AI_INTERNAL_USER_ID", "HOST_AI_INTERNAL_TENANT_ID",
        "HOST_AI_INTERNAL_ROLES", "HOST_AI_INTERNAL_SCOPES",
    ):
        monkeypatch.delenv(name, raising=False)

    http = client(tmp_path)
    article_preview = http.post("/api/v1/catalogo/preview", json={
        "dominio": "ARTICULO", "operacion": "CREAR", "session_id": "web",
        "payload": {"nombre": "Harina especial", "codigo": "ART-HARINA-HTTP", "unidad_base": "kg"},
    })
    assert article_preview.status_code == 200
    article_confirm = http.post("/api/v1/catalogo/confirmar", json={
        "preview_token": article_preview.json()["preview_token"], "session_id": "web",
    })
    assert article_confirm.status_code == 200
    article_id = article_confirm.json()["registro"]["codigo"]

    reread = http.get("/api/v1/articulos", params={"q": "Harina especial"})
    assert reread.status_code == 200
    assert any(item["id"] == article_id for item in reread.json()["catalogo"]["items"])

    recipe_preview = http.post("/api/v1/catalogo/preview", json={
        "dominio": "RECETA", "operacion": "MODIFICAR", "entity_id": recipe_id, "session_id": "web",
        "payload": {
            "ingredientes": ["Harina especial"], "cantidades": ["1 kg"],
            "ingredientes_estructurados": [{
                "nombre": "Harina especial", "cantidad": 1, "unidad": "kg",
                "article_id": article_id, "estado": "RESUELTO",
            }],
        },
    })
    assert recipe_preview.status_code == 200
    recipe_confirm = http.post("/api/v1/catalogo/confirmar", json={
        "preview_token": recipe_preview.json()["preview_token"], "session_id": "web",
    })
    assert recipe_confirm.status_code == 200
    saved = recipe_confirm.json()["registro"]
    assert saved["ingredientes_estructurados"][0]["article_id"] == article_id

    detail = http.get(f"/api/v1/biblioteca/elaboraciones/{recipe_id}")
    assert detail.status_code == 200
    assert article_id in json.dumps(detail.json())
    assert (stock_lotes.read_bytes(), stock_movimientos.read_bytes()) == stock_before


def test_article_ai_and_manual_reference_real_http_routes(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "DATOS/db"; db.mkdir(parents=True)
    (db / "articulos.json").write_text(json.dumps([{"codigo": "ART-CHAMP", "nombre": "Champiñones", "precio": None, "proveedor": "Proveedor real"}]), encoding="utf-8")
    monkeypatch.setenv("HOST_AI_INTERNAL_USER_ID", "CHEF"); monkeypatch.setenv("HOST_AI_INTERNAL_TENANT_ID", "LOCAL")
    monkeypatch.setenv("HOST_AI_INTERNAL_SCOPES", "articulos:write articulos:preview")
    platform = HostAIPlatformAPI(base_dir=tmp_path)
    platform.facade._article_docs_service = ArticuloDocumentacionWriteService(tmp_path, generator=FakeArticleGenerator())
    http = TestClient(create_app(platform_api=platform))

    proposal = http.post("/api/v1/articulos/ART-CHAMP/documentacion/propuesta", json={}).json()
    assert proposal["datos_propuestos_ia"] == {"familia": "Verduras"}
    preview = http.post("/api/v1/articulos/ART-CHAMP/documentacion/preview", json={"selected": proposal["datos_propuestos_ia"]}).json()
    confirmed = http.post("/api/v1/articulos/ART-CHAMP/documentacion/confirmar", json={"selected": proposal["datos_propuestos_ia"], "preview_token": preview["preview_token"]})
    assert confirmed.status_code == 200 and confirmed.json()["articulo"]["procedencia_campos"]["familia"]["tipo"] == "IA"

    manual = {"precio": 4, "cantidad_formato": 500, "unidad": "g"}
    manual_preview = http.post("/api/v1/articulos/ART-CHAMP/precio-referencia-manual/preview", json={"result": manual}).json()
    assert manual_preview["referencia_propuesta"]["precio_normalizado"] == 8
    manual_confirm = http.post("/api/v1/articulos/ART-CHAMP/precio-referencia-manual/confirmar", json={"result": manual, "preview_token": manual_preview["preview_token"]}).json()
    reread = http.get("/api/v1/articulos/ART-CHAMP").json()["articulo"]
    assert manual_confirm["precio_real_modificado"] is False and reread["precio"] is None
    assert reread["proveedor"] == "Proveedor real" and reread["precios_referencia"][-1]["tipo"] == "PRECIO_REFERENCIA_MANUAL"


def test_web_price_search_route_is_removed(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "DATOS/db"; db.mkdir(parents=True)
    (db / "articulos.json").write_text(json.dumps([{"codigo": "ART-CAVA", "nombre": "Cava para cocinar", "precio": None, "proveedor": "Proveedor real"}]), encoding="utf-8")
    monkeypatch.setenv("HOST_AI_INTERNAL_USER_ID", "CHEF"); monkeypatch.setenv("HOST_AI_INTERNAL_TENANT_ID", "LOCAL")
    monkeypatch.setenv("HOST_AI_INTERNAL_SCOPES", "articulos:write articulos:preview")
    http = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))
    paths = http.get("/openapi.json").json()["paths"]
    assert "/api/v1/articulos/precio-referencia-web/buscar" not in paths
