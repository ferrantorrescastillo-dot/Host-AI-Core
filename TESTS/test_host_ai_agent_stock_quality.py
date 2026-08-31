from __future__ import annotations

from types import SimpleNamespace

from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


class _Engine:
    def __init__(self, turns):
        self.turns = list(turns)
        self.requests = []

    def ejecutar_turn_agente(self, request):
        self.requests.append(request)
        return self.turns.pop(0)


class _StockExecutor:
    def __init__(self, data):
        self.data = data
        self.calls = []

    def execute_agent_read(self, tool_id, arguments):
        self.calls.append((tool_id, dict(arguments)))
        return SimpleNamespace(estado="OK", datos=self.data)


def _run_stock(data, final_text="Respuesta natural de Stock.", arguments=None):
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
            "consultar_estado_stock", arguments or {"consulta": "resumen"}, "stock-1"
        )]),
        AgentTurnResult(FINAL_RESPONSE, text=final_text),
    ])
    executor = _StockExecutor(data)
    result = HostAIAgent(
        engine,
        executor,
        HostAIToolCatalog(build_default_tool_registry()),
    ).run("consulta Stock")
    return result, engine, executor


def test_resumen_stock_consulta_tool_y_conserva_final_libre():
    text = "Tienes varias existencias registradas y conviene revisar las alertas."
    result, _engine, executor = _run_stock({
        "resumen": {"existencias": 3, "alertas": 1},
        "existencias": [], "alertas": [], "datos_reales_modificados": False,
    }, text)
    assert result.text == text
    assert executor.calls == [("consultar_estado_stock", {"consulta": "resumen"})]


def test_cantidad_y_unidad_llegan_intactas_al_segundo_turno():
    result, engine, _executor = _run_stock({
        "existencias": [{"article_id": "ART-P", "nombre": "Patata Monalisa", "cantidad": 3.75, "unidad": "kg"}],
        "alertas": [], "datos_reales_modificados": False,
    }, arguments={"consulta": "articulo", "termino": "Patata Monalisa"})
    tool_data = engine.requests[1].messages[-1]["content"]
    assert result.ok and tool_data["existencias"][0]["cantidad"] == 3.75
    assert tool_data["existencias"][0]["unidad"] == "kg"


def test_null_permanece_desconocido_y_no_se_convierte_en_cero():
    _result, engine, _executor = _run_stock({
        "existencias": [{"article_id": "ART-S", "nombre": "Salmon", "cantidad": None, "unidad": "kg"}],
        "alertas": [], "datos_reales_modificados": False,
    }, arguments={"consulta": "articulo", "termino": "Salmon"})
    tool_data = engine.requests[1].messages[-1]["content"]
    assert tool_data["existencias"][0]["cantidad"] is None
    assert "null significa desconocido o no registrado, nunca cero" in engine.requests[0].system_instructions


def test_alerta_sin_ubicacion_no_se_mezcla_con_bajo_minimo():
    _result, engine, _executor = _run_stock({
        "resumen": {"alertas": 1, "bajo_minimo": 0, "caducados": 0, "caducan_pronto": 0},
        "existencias": [],
        "alertas": [{"tipo": "sin_ubicacion", "nivel": "bajo", "mensaje": "Lote sin ubicacion"}],
        "datos_reales_modificados": False,
    }, arguments={"consulta": "alertas"})
    tool_data = engine.requests[1].messages[-1]["content"]
    assert tool_data["resumen"]["bajo_minimo"] == 0
    assert tool_data["alertas"][0]["tipo"] == "sin_ubicacion"
    assert "No conviertas una categoria de alerta en otra" in engine.requests[0].system_instructions


def test_suficiencia_requiere_referencia_y_follow_up_mantiene_articulo():
    engine = _Engine([AgentTurnResult(FINAL_RESPONSE, text="Necesitaria conocer tu consumo previsto.")])
    agent = HostAIAgent(
        engine, _StockExecutor({}), HostAIToolCatalog(build_default_tool_registry())
    )
    result = agent.run("Eso te parece suficiente?", conversation_context={"conversation_history": [
        {"role": "user", "content": "Cuanto stock tengo de Patata Monalisa?"},
        {"role": "assistant", "content": "Tienes 3,75 kg de Patata Monalisa registrados."},
    ]})
    assert result.executed_tools == []
    assert [item["role"] for item in engine.requests[0].messages] == ["user", "assistant", "user"]
    assert "No declares que una cantidad es suficiente o insuficiente" in engine.requests[0].system_instructions


def test_stock_catalogo_es_read_y_no_publica_modificacion():
    tools = HostAIToolCatalog(build_default_tool_registry()).effective_tools()
    stock = next(item for item in tools if item["tool_id"] == "consultar_estado_stock")
    assert stock["type"] == "READ" and stock["confirmation_policy"] == "NONE"
    assert all(not item["tool_id"].startswith(("crear_", "modificar_", "asignar_")) for item in tools)


def test_pregunta_general_no_necesita_stock():
    engine = _Engine([AgentTurnResult(FINAL_RESPONSE, text="Confitar usa grasa y baja temperatura; pochar busca coccion suave.")])
    result = HostAIAgent(
        engine, _StockExecutor({}), HostAIToolCatalog(build_default_tool_registry())
    ).run("Que diferencia hay entre confitar y pochar?")
    assert result.ok and result.executed_tools == []
