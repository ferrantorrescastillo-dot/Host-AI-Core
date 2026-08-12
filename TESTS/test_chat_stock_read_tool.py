from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from API.app import HostAIPlatformAPI
from API.contracts.http_models import ApiRequest
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.host_ai_deterministic_intent_router import (
    HostAIDeterministicIntentRouter,
    INTENT_CONSULTAR_ESTADO_STOCK,
)
from SERVICIOS.host_ai_engine.models import HostAIEngineRequest
from SERVICIOS.host_ai_engine.openai_provider import OpenAIProvider
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import TOOL_STATUS_ACTIVADA, build_default_tool_registry
from SERVICIOS.host_ai_tool_resolver import HostAIToolResolver
from TESTS.test_stock_dashboard_integration import _write_stock


class _HomeRead:
    def cargar_home(self):
        return {
            "modulos": {
                "stock": {
                    "estado": "datos_disponibles",
                    "estado_operativo": "revisar",
                    "total_existencias": 12,
                    "total_alertas": 12,
                    "total_lotes": 3,
                    "existencias": [
                        {"articulo_id": f"ART-{index}", "nombre": f"Articulo {index}", "cantidad": index, "unidad": "kg", "interno": "no_enviar"}
                        for index in range(12)
                    ],
                    "alertas": [
                        {"tipo": "bajo_stock", "nivel": "aviso", "mensaje": f"Alerta {index}", "path": "privado"}
                        for index in range(12)
                    ],
                    "resumen": {"bajo_minimo": 2, "caducados": 1, "caducan_pronto": 1},
                }
            }
        }


class _ArticlesRead:
    def __init__(self, items):
        self.items = list(items)

    def listar(self, query):
        term = str(query.get("q") or "").lower()
        found = [item for item in self.items if term in str(item.get("nombre") or "").lower()]
        return {"ok": True, "catalogo": {"items": found[:10], "total": len(found)}}


def _executor(items=None):
    return HostAIToolExecutor(
        build_default_tool_registry(),
        home_read_service=_HomeRead(),
        articulos_read_service=_ArticlesRead(items or []),
    )


def test_registry_y_resolver_autorizan_consulta_stock_como_read():
    registry = build_default_tool_registry()
    tool = registry.get("consultar_estado_stock")

    assert tool is not None
    assert tool.estado == TOOL_STATUS_ACTIVADA
    assert tool.tipo == "READ"
    assert tool.solo_lectura is True
    assert HostAIToolResolver().resolve(INTENT_CONSULTAR_ESTADO_STOCK) == "consultar_estado_stock"


def test_router_detecta_resumen_alertas_y_articulo():
    router = HostAIDeterministicIntentRouter()

    resumen = router.detectar("¿Cómo está el stock?")
    alertas = router.detectar("¿Qué productos tengo bajos de stock?")
    articulo = router.detectar("¿Cuánto stock tengo de Patata Monalisa?")
    articulo_sin_stock_literal = router.detectar("¿Tengo salmón?")

    assert resumen.intent == INTENT_CONSULTAR_ESTADO_STOCK
    assert resumen.terms["consulta"] == "resumen"
    assert alertas.terms["consulta"] == "alertas"
    assert articulo.terms == {"consulta": "articulo", "termino": "patata monalisa"}
    assert articulo_sin_stock_literal.terms == {"consulta": "articulo", "termino": "salmon"}


def test_executor_limita_y_sanea_resultado_stock():
    result = _executor().execute("consultar_estado_stock", {"consulta": "resumen"})

    assert result.estado == "OK"
    assert len(result.datos["existencias"]) == 10
    assert len(result.datos["alertas"]) == 10
    assert result.datos["fuente"] == "stock_canonico"
    assert result.datos["solo_lectura"] is True
    assert result.datos["datos_reales_modificados"] is False
    assert "interno" not in result.datos["existencias"][0]
    assert "path" not in result.datos["alertas"][0]


def test_executor_articulo_existente_inexistente_y_ambiguo():
    items = [
        {"id": "ART-P", "nombre": "Patata Monalisa", "stock": 0.5, "unidad_stock": "kg"},
        {"id": "ART-S1", "nombre": "Salmon fresco", "stock": 2, "unidad_stock": "kg"},
        {"id": "ART-S2", "nombre": "Salmon ahumado", "stock": None, "unidad": "kg"},
    ]
    executor = _executor(items)

    existing = executor.execute("consultar_estado_stock", {"consulta": "articulo", "termino": "Patata Monalisa"})
    missing = executor.execute("consultar_estado_stock", {"consulta": "articulo", "termino": "Merluza"})
    ambiguous = executor.execute("consultar_estado_stock", {"consulta": "articulo", "termino": "Salmon"})

    assert existing.datos["estado"] == "OK"
    assert existing.datos["existencias"] == [{"article_id": "ART-P", "nombre": "Patata Monalisa", "cantidad": 0.5, "unidad": "kg"}]
    assert missing.datos["estado"] == "NO_ENCONTRADO"
    assert missing.datos["existencias"] == []
    assert ambiguous.datos["estado"] == "AMBIGUO"
    assert len(ambiguous.datos["existencias"]) == 2


def test_executor_no_permite_write_por_ruta_read():
    result = _executor().execute("crear_receta", {"consulta": "resumen"})

    assert result.estado == "DESHABILITADA"


class _FakeResponses:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text="Stock explicado sin cambiar cifras")


def test_openai_recibe_contexto_determinista_saneado(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "credencial-ficticia")
    responses = _FakeResponses()
    provider = OpenAIProvider(client_factory=lambda **_kwargs: SimpleNamespace(responses=responses))
    context = {
        "resumen": {"existencias": 2},
        "existencias": [{"article_id": "ART-1", "cantidad": 0.5, "unidad": "kg"}],
        "fuente": "stock_canonico",
        "solo_lectura": True,
    }
    request = HostAIEngineRequest(
        origen="CHAT",
        modulo="chat_host_ai",
        tipo_peticion="consulta_stock",
        datos_enviados={"pregunta": "¿Cómo está el stock?", "tool_context": context},
        proveedor_preferido="OPENAI",
    )

    result = provider.ejecutar(request)

    assert result.ok is True
    sent = responses.calls[0]["input"]
    assert '"cantidad": 0.5' in sent
    assert '"unidad": "kg"' in sent
    assert "exclusivamente este contexto" in sent
    assert "no recalcules cifras" in sent.lower()


class _Orchestrator:
    def __init__(self, engine_result):
        self.host_ai_engine = SimpleNamespace(default_provider="OPENAI")
        self.engine_result = engine_result
        self.requests = []

    def resolver(self, request):
        self.requests.append(request)
        return SimpleNamespace(to_dict=lambda: {"datos": {"host_ai_engine": self.engine_result}})


def test_chat_ejecuta_stock_antes_de_openai_y_conserva_dto():
    engine = {"estado": "OK", "proveedor": "OPENAI", "respuesta": {"mensaje": "Respuesta natural"}, "errores": []}
    orchestrator = _Orchestrator(engine)
    chat = ServicioChatHostAIShell(orchestrator, home_read_service=_HomeRead())
    chat.tool_executor = _executor([{"id": "ART-P", "nombre": "Patata Monalisa", "stock": 0.5, "unidad_stock": "kg"}])

    response = chat.enviar("¿Cuánto stock tengo de Patata Monalisa?")

    request_data = orchestrator.requests[0].parametros["datos_enviados"]
    assert request_data["tool_context"]["existencias"][0]["cantidad"] == 0.5
    assert response["mensaje"] == "Respuesta natural"
    assert response["datos"]["tool_context"]["existencias"][0]["cantidad"] == 0.5
    assert response["datos"]["datos_reales_modificados"] is False


def test_chat_usa_fallback_determinista_si_openai_falla():
    engine = {"estado": "ERROR", "proveedor": "OPENAI", "respuesta": {}, "errores": ["fallo_controlado"]}
    chat = ServicioChatHostAIShell(_Orchestrator(engine), home_read_service=_HomeRead())
    chat.tool_executor = _executor([{"id": "ART-P", "nombre": "Patata Monalisa", "stock": 0.5, "unidad_stock": "kg"}])

    response = chat.enviar("Dime el stock de Patata Monalisa")

    assert response["ok"] is True
    assert "0.5 kg" in response["mensaje"]
    assert response["datos"]["tool_context"]["fuente"] == "stock_canonico"


def _write_articles(base: Path) -> None:
    db = base / "DATOS" / "db"
    db.mkdir(parents=True, exist_ok=True)
    (db / "articulos.json").write_text(
        json.dumps([{"codigo": "ART-WEB-1", "nombre": "Tomate", "unidad_base": "kg", "activo": True}]),
        encoding="utf-8",
    )
    (db / "compras_producto_proveedor.json").write_text("[]", encoding="utf-8")
    (base / "DATOS" / "facturas").mkdir(parents=True, exist_ok=True)
    (base / "DATOS" / "facturas" / "historico_precios.json").write_text('{"registros": []}', encoding="utf-8")


def test_post_chat_stock_ruta_http_real_no_modifica_stock(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("HOST_AI_AI_PROVIDER", "SIMULADO")
    _write_stock(tmp_path)
    _write_articles(tmp_path)
    stock_files = [
        tmp_path / "DATOS" / "db" / "stock_lotes.json",
        tmp_path / "DATOS" / "db" / "stock_movimientos.json",
    ]
    before = {path: path.read_bytes() for path in stock_files}

    response = HostAIPlatformAPI(base_dir=tmp_path).handle(
        ApiRequest(method="POST", path="/api/v1/chat", body={"mensaje": "Dime el stock de Tomate", "contexto": {}})
    )

    assert response.status_code == 200
    assert response.payload["ok"] is True
    assert response.payload["datos_reales_modificados"] is False
    tool_context = response.payload["chat"]["datos"]["tool_context"]
    assert tool_context["existencias"][0]["article_id"] == "ART-WEB-1"
    assert tool_context["existencias"][0]["cantidad"] == 4
    assert all(path.read_bytes() == before[path] for path in stock_files)
