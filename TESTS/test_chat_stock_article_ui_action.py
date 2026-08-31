from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentRunResult, AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


class _HomeRead:
    def cargar_home(self):
        return {
            "modulos": {
                "stock": {
                    "estado_operativo": "revisar",
                    "total_existencias": 5,
                    "total_alertas": 8,
                    "total_lotes": 13,
                    "existencias": [
                        {"articulo_id": "ART-ARROZ", "nombre": "Arroz bomba", "cantidad": 3, "unidad": "kg"},
                        {"articulo_id": "ART-PATATA", "nombre": "Patata Monalisa", "cantidad": 3.75, "unidad": "kg"},
                    ],
                    "alertas": [],
                    "resumen": {},
                }
            }
        }


class _ArticlesRead:
    def __init__(self):
        self.items = [
            {"id": "ART000006", "nombre": "A.P BROCHETA DE GAMBA XL", "stock": None, "unidad": "kg"},
            {"id": "ART000351", "nombre": "Ensaladilla de Gamba", "stock": None, "unidad": "kg"},
            {"id": "ART000323", "nombre": "Gamba paella", "stock": None, "unidad": "kg"},
        ]

    def listar(self, query):
        term = str(query.get("q") or "").casefold()
        matches = [item for item in self.items if term in f"{item['id']} {item['nombre']}".casefold()]
        return {"ok": True, "catalogo": {"items": matches, "total": len(matches)}}

    def obtener(self, article_id):
        item = next((item for item in self.items if item["id"] == article_id), None)
        return {"ok": item is not None, "articulo": item}


class _Engine:
    def __init__(self, turns):
        self.turns = list(turns)
        self.requests = []

    def ejecutar_turn_agente(self, request):
        self.requests.append(request)
        return self.turns.pop(0)


def _executor():
    return HostAIToolExecutor(
        build_default_tool_registry(),
        home_read_service=_HomeRead(),
        articulos_read_service=_ArticlesRead(),
    )


def test_termino_fuerza_filtro_de_articulo_y_separa_resumen_global():
    executor = _executor()
    before = deepcopy(executor.articulos_read_service.items)

    result = executor.execute_agent_read(
        "consultar_estado_stock", {"consulta": "resumen", "termino": "gamba"},
    )

    assert result.estado == "OK"
    assert result.datos["consulta"] == "articulo"
    assert result.datos["estado"] == "AMBIGUO"
    assert result.datos["ambito_resultados"] == "FILTRADO_POR_TERMINO"
    assert [item["article_id"] for item in result.datos["resultados_filtrados"]] == [
        "ART000006", "ART000351", "ART000323",
    ]
    assert result.datos["existencias"] == result.datos["resultados_filtrados"]
    assert result.datos["resumen_global"]["existencias"] == 5
    assert "resumen" not in result.datos
    assert all(item["nombre"] not in {"Arroz bomba", "Patata Monalisa"} for item in result.datos["resultados_filtrados"])
    assert executor.articulos_read_service.items == before
    assert result.datos["datos_reales_modificados"] is False


def test_peticion_mostrar_stock_resuelve_y_abre_articulo_sin_confirmacion():
    registry = build_default_tool_registry()
    executor = _executor()
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
            "consultar_estado_stock", {"consulta": "articulo", "termino": "Gamba paella"}, "read-stock",
        )]),
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
            "abrir_articulo", {"articulo_id": "ART000323", "vista": "ficha"}, "open-article",
        )]),
        AgentTurnResult(FINAL_RESPONSE, text="Te he abierto la ficha de Gamba paella en una nueva pestaña."),
    ])

    result = HostAIAgent(
        engine, executor, HostAIToolCatalog.for_general_agent(registry),
    ).run("Enséñame el stock de Gamba paella.")

    assert result.ok is True
    assert result.executed_tools == ["consultar_estado_stock", "abrir_articulo"]
    assert result.ui_actions == [{
        "type": "OPEN_VIEW", "target": "ARTICULO", "id": "ART000323",
        "view": "FICHA", "label": "Gamba paella", "safe": True,
        "datos_reales_modificados": False,
    }]
    assert len(result.text.split()) < 15
    assert "¿Quieres" not in result.text
    assert result.datos_reales_modificados is False
    assert engine.requests[1].limits["max_tool_calls"] == 4
    assert any(item.get("tool_id") == "consultar_estado_stock" for item in engine.requests[1].messages)


def test_contratos_publicados_distinguen_filtro_y_apertura_explicita():
    tools = HostAIToolCatalog.for_general_agent(build_default_tool_registry()).effective_tools()
    stock = next(item for item in tools if item["tool_id"] == "consultar_estado_stock")
    opening = next(item for item in tools if item["tool_id"] == "abrir_articulo")

    assert "consulta=articulo" in stock["description"]
    assert "nombre, código o término concreto" in stock["input_schema"]["properties"]["consulta"]["description"]
    assert "ver el artículo o su stock" in opening["description"]
    assert "sin pedir una confirmación adicional" in opening["description"]
    assert opening["type"] == "UI_ACTION"
    assert opening["confirmation_policy"] == "NONE"


def test_consulta_read_concreta_no_genera_ui_action_por_si_sola():
    registry = build_default_tool_registry()
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
            "consultar_estado_stock", {"consulta": "articulo", "termino": "Gamba paella"}, "read-only",
        )]),
        AgentTurnResult(FINAL_RESPONSE, text="La cantidad de Gamba paella no está registrada."),
    ])

    result = HostAIAgent(
        engine, _executor(), HostAIToolCatalog.for_general_agent(registry),
    ).run("¿Cuánto stock queda de Gamba paella?")

    assert result.executed_tools == ["consultar_estado_stock"]
    assert result.ui_actions == []
    assert result.datos_reales_modificados is False


def test_follow_up_stock_sin_termino_reutiliza_articulo_activo():
    registry = build_default_tool_registry()
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
            "consultar_estado_stock", {"consulta": "articulo"}, "read-contextual",
        )]),
        AgentTurnResult(FINAL_RESPONSE, text="La cantidad no está registrada."),
    ])

    result = HostAIAgent(
        engine, _executor(), HostAIToolCatalog.for_general_agent(registry),
    ).run(
        "¿Cuánto nos queda?",
        {"active_entity": {"id": "ART000323", "tipo": "ARTICULO", "nombre": "Gamba paella"}},
    )

    assert result.executed_tools == ["consultar_estado_stock"]
    assert result.ui_actions == []
    tool_data = engine.requests[1].messages[-1]["content"]
    assert tool_data["consulta"] == "articulo"
    assert tool_data["termino"] == "ART000323"
    assert tool_data["estado"] == "OK"
    assert tool_data["existencias"][0]["article_id"] == "ART000323"
    assert tool_data["existencias"][0]["cantidad"] is None
    assert tool_data["resumen_global"]["existencias"] == 5


def test_follow_up_conserva_articulo_abierto_y_el_read_posterior_no_reabre(monkeypatch):
    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()))
    shell.agent_observability = SimpleNamespace(emit=lambda *_args, **_kwargs: None)
    captured = []
    results = iter([
        AgentRunResult(True, "He encontrado varios artículos.", "HAA-1", "FAKE", "fake", 2, ["consultar_estado_stock"]),
        AgentRunResult(True, "Te he abierto Gamba paella.", "HAA-2", "FAKE", "fake", 3,
                       ["consultar_estado_stock", "abrir_articulo"], ui_actions=[{
                           "type": "OPEN_VIEW", "target": "ARTICULO", "id": "ART000323",
                           "view": "FICHA", "label": "Gamba paella",
                       }]),
        AgentRunResult(True, "La cantidad no está registrada.", "HAA-3", "FAKE", "fake", 2,
                       ["consultar_estado_stock"]),
    ])

    def fake_run(_message, conversation_context=None):
        captured.append(deepcopy(conversation_context or {}))
        return next(results)

    monkeypatch.setattr(shell.general_agent, "run", fake_run)
    ambiguous = shell.enviar("Enséñame el stock de gamba.")
    selected = shell.enviar("Me refiero a Gamba paella.")
    remaining = shell.enviar("¿Cuánto nos queda?")

    assert ambiguous["datos"]["ui_action"] is None
    assert selected["datos"]["ui_action"]["id"] == "ART000323"
    assert captured[2]["active_entity"]["id"] == "ART000323"
    assert remaining["datos"]["ui_action"] is None
    assert remaining["datos"]["datos_reales_modificados"] is False
