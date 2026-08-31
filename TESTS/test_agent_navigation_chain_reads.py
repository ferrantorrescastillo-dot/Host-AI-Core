import json
from pathlib import Path
from types import SimpleNamespace

from SERVICIOS.articulos_catalog_read_service import ArticulosCatalogReadService
from SERVICIOS.host_ai_compras_read_service import HostAIComprasReadService
from SERVICIOS.host_ai_escandallos_read_service import HostAIEscandallosReadService
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


def test_articulo_busqueda_parcial_y_detalle_sin_escritura(tmp_path: Path):
    db = tmp_path / "DATOS" / "db"; db.mkdir(parents=True)
    (db / "articulos.json").write_text(json.dumps([{"codigo": "ART-PAT", "nombre": "Patata Monalisa", "unidad_base": "kg", "precio": 2}]), encoding="utf-8")
    service = ArticulosCatalogReadService(tmp_path)
    search = service.listar({"q": "monalisa", "page": 1, "page_size": 10})
    detail = service.obtener("ART-PAT")
    assert search["catalogo"]["items"][0]["id"] == "ART-PAT"
    assert detail["articulo"]["unidad_base"] == "kg"


def test_compras_filtra_lineas_por_article_id():
    compras = SimpleNamespace(
        listar_pedidos=lambda: [{"id": "PED-1", "proveedor": "P", "estado": "preparado", "lineas": [{"id": "L1", "articulo_id": "ART-PAT", "nombre": "Patata", "cantidad": 2, "unidad": "kg", "precio_unitario": 1}, {"id": "L2", "articulo_id": "ART-OTRO", "nombre": "Otro", "cantidad": 1, "unidad": "u", "precio_unitario": 1}]}],
        listar_recepciones=lambda pedido_id: [],
    )
    result = HostAIComprasReadService(SimpleNamespace(compras=compras)).consultar_pedidos(article_id="ART-PAT")
    assert result["pedidos"][0]["lineas"] == [{"articulo_id": "ART-PAT", "nombre": "Patata", "pedido": 2.0, "recibido": 0.0, "pendiente": 2.0, "unidad": "kg"}]


def test_fallback_culinario_usa_nombre_asociado_y_conserva_procedencia(tmp_path: Path):
    db = tmp_path / "DATOS" / "db"; db.mkdir(parents=True)
    (db / "escandallos_canonicos.json").write_text(json.dumps({"escandallos": [{"receta": {"codigo": "REC-REAL", "nombre": "Carrillera de ternera", "rendimiento": 4, "unidad_rendimiento": "u", "ingredientes": []}, "coste_total": 0}]}), encoding="utf-8")
    result = HostAIEscandallosReadService(tmp_path).consultar("detalle", escandallo_id="REC-HISTORICO", nombre_referencia="Carrillera de ternera")
    assert result["estado"] == "OK"
    assert result["referencia_original"] == "REC-HISTORICO"
    assert result["metodo_resolucion"] == "NOMBRE_REFERENCIA"


def test_catalogo_general_expone_receta_articulo_stock_y_compras():
    ids = {item["tool_id"] for item in HostAIToolCatalog.for_general_agent(build_default_tool_registry()).effective_tools()}
    assert {"consultar_escandallos", "buscar_articulos", "consultar_articulo_detalle", "consultar_estado_stock", "consultar_compras_pendientes", "consultar_produccion"} <= ids