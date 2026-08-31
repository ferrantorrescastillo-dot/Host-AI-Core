from __future__ import annotations

from types import SimpleNamespace

from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnResult, FINAL_RESPONSE


class _Engine:
    def __init__(self, text="Respuesta natural."):
        self.text = text
        self.requests = []

    def ejecutar_turn_agente(self, request):
        self.requests.append(request)
        return AgentTurnResult(FINAL_RESPONSE, text=self.text)


class _Catalog:
    def __init__(self, tools):
        self.tools = tools

    def effective_tools(self):
        return list(self.tools)


class _Executor:
    def execute_agent_read(self, *_args):
        raise AssertionError("No se esperaba ejecutar tools")


def _tool(tool_id, description, capability_type="READ"):
    return {
        "tool_id": tool_id,
        "description": description,
        "type": capability_type,
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        "enabled": True,
        "confirmation_policy": "NONE",
    }


def test_contrato_comunica_catalogo_read_y_ausencia_de_write():
    engine = _Engine()
    tools = [
        _tool("consultar_produccion", "Consultar el estado actual de Produccion."),
        _tool("consultar_estado_stock", "Consultar existencias y alertas de Stock."),
        _tool("consultar_compras_pendientes", "Consultar pedidos pendientes de Compras."),
    ]

    HostAIAgent(engine, _Executor(), _Catalog(tools)).run("Como voy?")

    request = engine.requests[0]
    assert request.allowed_tools == tools
    assert request.system_instructions.count("- READ:") == 3
    assert "Esta lista es exhaustiva para este turno" in request.system_instructions
    assert "- WRITE:" not in request.system_instructions


def test_catalogo_actual_no_publica_write_recetas_ni_personal():
    from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
    from SERVICIOS.host_ai_tool_registry import build_default_tool_registry

    tools = HostAIToolCatalog(build_default_tool_registry()).effective_tools()
    serialized = " ".join(f"{item['tool_id']} {item['description']}" for item in tools).lower()

    assert tools and all(item["type"] == "READ" for item in tools)
    assert "abrir_elaboracion" not in {item["tool_id"] for item in tools}
    assert all(value not in serialized for value in ("recepcionar", "confirmar", "receta", "personal"))


def test_capability_futura_aparece_automaticamente_sin_cambiar_identidad():
    base_tool = _tool("consultar_estado_stock", "Consultar Stock.")
    future_tool = _tool("buscar_recetas", "Buscar recetas autorizadas.")
    base_engine = _Engine()
    future_engine = _Engine()

    HostAIAgent(base_engine, _Executor(), _Catalog([base_tool])).run("consulta")
    HostAIAgent(future_engine, _Executor(), _Catalog([base_tool, future_tool])).run("consulta")

    base_instructions = base_engine.requests[0].system_instructions
    future_instructions = future_engine.requests[0].system_instructions
    assert "Buscar recetas autorizadas." not in base_instructions
    assert "- READ: Buscar recetas autorizadas." in future_instructions
    assert future_instructions.startswith(HostAIAgent.SYSTEM_INSTRUCTIONS)


def test_capability_compuesta_incompleta_exige_todas_sus_fuentes():
    engine = _Engine()
    tools = [
        _tool("consultar_produccion", "Consultar Produccion."),
        _tool("consultar_estado_stock", "Consultar Stock."),
    ]

    HostAIAgent(engine, _Executor(), _Catalog(tools)).run("consulta")

    instructions = engine.requests[0].system_instructions
    assert "todas las capacidades necesarias" in instructions
    assert "Disponer de una parte no autoriza a prometer el conjunto" in instructions
    assert "Recetas" not in instructions and "Ingredientes" not in instructions
    assert [tool["tool_id"] for tool in engine.requests[0].allowed_tools] == [
        "consultar_produccion", "consultar_estado_stock"
    ]


def test_capability_compuesta_completa_refleja_todas_sin_cambiar_politica():
    engine = _Engine()
    tools = [
        _tool("consultar_produccion", "Consultar Produccion."),
        _tool("buscar_recetas", "Consultar Recetas e ingredientes."),
        _tool("consultar_estado_stock", "Consultar Stock."),
    ]

    HostAIAgent(engine, _Executor(), _Catalog(tools)).run("consulta")

    instructions = engine.requests[0].system_instructions
    assert all(f"- READ: {tool['description']}" in instructions for tool in tools)
    assert instructions.count("- READ:") == 3
    assert "todas las capacidades necesarias" in instructions


def test_datos_operativos_no_se_derivan_del_conocimiento_general():
    engine = _Engine()
    HostAIAgent(
        engine,
        _Executor(),
        _Catalog([_tool("consultar_produccion", "Consultar Produccion.")]),
    ).run("consulta")

    instructions = engine.requests[0].system_instructions
    assert "Distingue tu conocimiento general de los datos operativos actuales" in instructions
    assert "capability autorizada ejecutada" in instructions
    assert all(value not in instructions for value in ("consultar_personal", "consultar_maquinaria"))


def test_read_only_distingue_recomendar_de_ejecutar():
    engine = _Engine()
    HostAIAgent(
        engine,
        _Executor(),
        _Catalog([_tool("consultar_operacion", "Consultar informacion operativa.")]),
    ).run("Que harias primero?")

    instructions = engine.requests[0].system_instructions
    assert "Una capability READ solo permite consultar su informacion" in instructions
    assert "Distingue recomendar al usuario una accion de ofrecer ejecutarla tu" in instructions
    assert "solo puedes ofrecer ejecutar una operacion si el catalogo contiene" in instructions


def test_sin_escandallo_no_habilita_diagnostico_reparacion_ni_propuesta_de_escritura():
    engine = _Engine()
    HostAIAgent(
        engine,
        _Executor(),
        _Catalog([_tool("consultar_escandallos", "Consultar costes de escandallos.")]),
    ).run("Por que esta incompleto?")

    instructions = engine.requests[0].system_instructions
    assert "En estado SIN_ESCANDALLO limita la causa" in instructions
    assert "no ofrezcas buscar en Stock" in instructions
    assert "no ofrezcas preparar o crear un escandallo" in instructions
    assert "Consulta ingredientes solo cuando el usuario lo pida explicitamente" in instructions


def test_general_agent_no_publica_preparacion_preview_confirmacion_ni_write_de_escandallos():
    from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
    from SERVICIOS.host_ai_tool_registry import build_default_tool_registry

    tools = HostAIToolCatalog.for_general_agent(build_default_tool_registry()).effective_tools()
    escandallo_tools = [
        item for item in tools
        if "escandall" in f"{item['tool_id']} {item['description']}".lower()
    ]

    assert {item["tool_id"] for item in escandallo_tools} == {
        "consultar_escandallos", "consultar_uso_elaboracion", "abrir_elaboracion",
    }
    assert {item["type"] for item in escandallo_tools} == {"READ", "UI_ACTION"}
    assert all(item["type"] not in {"PREVIEW", "CONFIRM", "WRITE"} for item in escandallo_tools)


def test_recursos_y_tiempos_ausentes_no_son_datos_operativos_conocidos():
    engine = _Engine()
    HostAIAgent(
        engine,
        _Executor(),
        _Catalog([_tool("consultar_operacion", "Consultar informacion operativa.")]),
    ).run("consulta")

    instructions = engine.requests[0].system_instructions
    assert "recursos, responsables, equipos, disponibilidad, dependencias" in instructions
    assert "duraciones operativas" in instructions
    assert "Si una recomendacion depende de informacion ausente, expresala condicionalmente" in instructions
    assert "no convertirla en un hecho operativo" in instructions


def test_capability_write_futura_aparece_y_habilita_solo_su_operacion():
    engine = _Engine()
    tools = [
        _tool("consultar_pedidos", "Consultar pedidos.", "READ"),
        _tool("actualizar_pedido", "Actualizar un pedido autorizado.", "WRITE"),
    ]

    HostAIAgent(engine, _Executor(), _Catalog(tools)).run("consulta")

    request = engine.requests[0]
    assert "- READ: Consultar pedidos." in request.system_instructions
    assert "- WRITE: Actualizar un pedido autorizado." in request.system_instructions
    assert request.allowed_tools == tools
    assert "con un tipo que permita ejecutarla" in request.system_instructions


def test_recomendacion_libre_y_pregunta_general_conservan_texto_sin_tools():
    recommendation = "Yo revisaria primero el bloqueo y, si depende de material, comprobaria su disponibilidad."
    recommendation_engine = _Engine(recommendation)
    recommendation_agent = HostAIAgent(
        recommendation_engine,
        _Executor(),
        _Catalog([_tool("consultar_operacion", "Consultar informacion operativa.")]),
    )
    assert recommendation_agent.run("Que harias primero?").text == recommendation

    general = "Confitar cocina lentamente en grasa; pochar cocina suavemente sin buscar dorado."
    general_engine = _Engine(general)
    general_agent = HostAIAgent(general_engine, _Executor(), _Catalog([]))
    result = general_agent.run("Que diferencia hay entre confitar y pochar?")
    assert result.text == general
    assert result.executed_tools == []


def test_texto_final_breve_llega_intacto_y_follow_up_se_conserva():
    text = "Yo empezaria por aclarar el bloqueo."
    engine = _Engine(text)
    agent = HostAIAgent(engine, _Executor(), _Catalog([_tool("consultar_produccion", "Consultar Produccion.")]))

    result = agent.run(
        "Y tu que harias primero?",
        conversation_context={"conversation_history": [
            {"role": "user", "content": "Como voy?"},
            {"role": "assistant", "content": "Hay una tarea bloqueada."},
        ]},
    )

    assert result.text == text
    assert engine.requests[0].messages == [
        {"role": "user", "content": "Como voy?"},
        {"role": "assistant", "content": "Hay una tarea bloqueada."},
        {"role": "user", "content": "Y tu que harias primero?"},
    ]
