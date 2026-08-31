from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentRunResult, AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_agent_policy import HostAIAgentPolicy
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


class _Escandallos:
    def __init__(self):
        self.state = {
            "REC-ENSALADILLA": {"nombre": "Ensaladilla de gamba", "tiene_escandallo": True},
            "REC601-000001": {"nombre": "SALSA DE CAVA", "tiene_escandallo": False},
        }

    def consultar(self, consulta, *, escandallo_id="", **_kwargs):
        item = self.state.get(escandallo_id)
        return {
            "estado": "OK" if item else "NO_ENCONTRADO",
            "elaboracion": {"id": escandallo_id, **item} if item else None,
            "solo_lectura": True, "datos_reales_modificados": False,
        }


class _Engine:
    def __init__(self, turns):
        self.turns = list(turns)
        self.requests = []

    def ejecutar_turn_agente(self, request):
        self.requests.append(request)
        return self.turns.pop(0)


def _run_view(view: str, message: str | None = None):
    registry = build_default_tool_registry()
    service = _Escandallos()
    executor = HostAIToolExecutor(registry, escandallos_read_service=service)
    before = deepcopy(service.state)
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
            "consultar_escandallos", {"consulta": "detalle", "escandallo_id": "REC-ENSALADILLA"}, "read-1",
        )]),
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
            "abrir_elaboracion", {"elaboracion_id": "REC-ENSALADILLA", "vista": view}, "ui-1",
        )]),
        AgentTurnResult(FINAL_RESPONSE, text="Te he abierto la ficha de Ensaladilla de gamba."),
    ])
    result = HostAIAgent(
        engine, executor, HostAIToolCatalog.for_general_agent(registry),
    ).run(message or "Enséñame la ficha de la ensaladilla.")
    return result, engine, before, service.state


def test_receta_resuelve_identidad_y_emite_ui_action_segura() -> None:
    result, engine, before, after = _run_view("receta")
    assert result.ok and result.executed_tools == ["consultar_escandallos", "abrir_elaboracion"]
    assert result.ui_actions == [{
        "type": "OPEN_VIEW", "target": "ELABORACION", "id": "REC-ENSALADILLA",
        "view": "RECETA", "label": "Ensaladilla de gamba", "safe": True,
        "datos_reales_modificados": False,
    }]
    assert before == after and result.datos_reales_modificados is False
    assert any(item.get("type") == "TOOL_DATA" for item in engine.requests[-1].messages)


def test_escandallo_emite_la_vista_correcta() -> None:
    result, _engine, before, after = _run_view(
        "escandallo", "Enséñame el escandallo de la ensaladilla.",
    )
    assert result.ui_actions[0]["view"] == "ESCANDALLO"
    assert before == after


def test_receta_sin_escandallo_abre_receta_pero_no_inventa_vista_economica() -> None:
    executor = HostAIToolExecutor(
        build_default_tool_registry(), escandallos_read_service=_Escandallos(),
    )

    recipe = executor.execute_agent_ui_action("abrir_elaboracion", {
        "elaboracion_id": "REC601-000001", "vista": "receta",
    })
    costing = executor.execute_agent_ui_action("abrir_elaboracion", {
        "elaboracion_id": "REC601-000001", "vista": "escandallo",
    })

    assert recipe.estado == "OK"
    assert recipe.acciones[0] == {
        "type": "OPEN_VIEW", "target": "ELABORACION", "id": "REC601-000001",
        "view": "RECETA", "label": "SALSA DE CAVA", "safe": True,
        "datos_reales_modificados": False,
    }
    assert costing.estado == "ERROR" and costing.errores == ["escandallo_not_found"]
    assert costing.acciones == []
    assert costing.datos["estado"] == "ESCANDALLO_NO_ENCONTRADO"
    assert costing.datos["estado_coste"] == "SIN_ESCANDALLO"
    assert costing.datos["datos_reales_modificados"] is False


def test_provider_adversarial_no_abre_receta_ni_inventa_write_si_falta_escandallo() -> None:
    registry = build_default_tool_registry()
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
            "abrir_elaboracion", {"elaboracion_id": "REC601-000001", "vista": "escandallo"},
            "missing-escandallo",
        )]),
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
            "abrir_elaboracion", {"elaboracion_id": "REC601-000001", "vista": "receta"},
            "fallback-recipe",
        )]),
        AgentTurnResult(FINAL_RESPONSE, text=(
            "He abierto la receta y también puedo guardar un escandallo ahora."
        )),
    ])
    result = HostAIAgent(
        engine,
        HostAIToolExecutor(registry, escandallos_read_service=_Escandallos()),
        HostAIToolCatalog.for_general_agent(registry),
    ).run("Abre el escandallo de SALSA DE CAVA")

    assert result.text == "SALSA DE CAVA no tiene un escandallo registrado."
    assert result.ui_actions == []
    assert result.executed_tools == []
    assert all(term not in result.text.lower() for term in ("he abierto", "receta", "guardar", "preparar"))
    rejected = next(
        item for item in engine.requests[-1].messages
        if item.get("type") == "TOOL_DATA" and item.get("call_id") == "fallback-recipe"
    )
    assert rejected["content"]["reason"] == "requested_view_mismatch"
    assert result.datos_reales_modificados is False


def test_contrato_obliga_navegacion_explicita_sin_segunda_confirmacion() -> None:
    result, engine, _before, _after = _run_view(
        "receta", "Enséñame la receta de la ensaladilla.",
    )
    instructions = engine.requests[0].system_instructions
    action = next(
        item for item in engine.requests[0].allowed_tools
        if item["tool_id"] == "abrir_elaboracion"
    )

    assert result.executed_tools == ["consultar_escandallos", "abrir_elaboracion"]
    assert result.ui_actions[0]["view"] == "RECETA"
    assert "ejecutala directamente" in instructions
    assert "no requiere una segunda confirmacion" in instructions
    assert "sin pedir una confirmación adicional" in action["description"]
    assert "¿Quieres que" not in result.text
    assert len(result.text.split()) < 15
    assert "no reproduzcas el contenido completo" in instructions


def test_identidad_contextual_permite_abrir_receta_sin_repetir_read() -> None:
    registry = build_default_tool_registry()
    service = _Escandallos()
    executor = HostAIToolExecutor(registry, escandallos_read_service=service)
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
            "abrir_elaboracion", {"elaboracion_id": "REC-ENSALADILLA", "vista": "receta"}, "ui-context",
        )]),
        AgentTurnResult(FINAL_RESPONSE, text="Te he abierto la receta de Ensaladilla de gamba."),
    ])

    result = HostAIAgent(
        engine, executor, HostAIToolCatalog.for_general_agent(registry),
    ).run("Enséñame la receta.", conversation_context={
        "active_entity": {"id": "REC-ENSALADILLA", "nombre": "Ensaladilla de gamba"},
    })

    assert result.executed_tools == ["abrir_elaboracion"]
    assert result.ui_actions[0]["id"] == "REC-ENSALADILLA"
    assert any(
        item.get("role") == "developer" and "REC-ENSALADILLA" in item.get("content", "")
        for item in engine.requests[0].messages
    )


def test_consulta_sin_intencion_de_abrir_no_exige_ui_action() -> None:
    registry = build_default_tool_registry()
    service = _Escandallos()
    executor = HostAIToolExecutor(registry, escandallos_read_service=service)
    for message in ("¿Cuánto cuesta la ensaladilla?", "¿Qué ingredientes tiene?"):
        engine = _Engine([
            AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall(
                "consultar_escandallos", {"consulta": "detalle", "escandallo_id": "REC-ENSALADILLA"}, "read-only",
            )]),
            AgentTurnResult(FINAL_RESPONSE, text="Respuesta basada en el escandallo."),
        ])
        result = HostAIAgent(
            engine, executor, HostAIToolCatalog.for_general_agent(registry),
        ).run(message)
        assert result.executed_tools == ["consultar_escandallos"]
        assert result.ui_actions == []


def test_abrir_y_analizar_conserva_ui_action_y_respuesta_fundamentada() -> None:
    registry = build_default_tool_registry()
    service = _Escandallos()
    executor = HostAIToolExecutor(registry, escandallos_read_service=service)
    engine = _Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[
            ToolCall("consultar_escandallos", {"consulta": "detalle", "escandallo_id": "REC-ENSALADILLA"}, "read-analysis"),
            ToolCall("abrir_elaboracion", {"elaboracion_id": "REC-ENSALADILLA", "vista": "escandallo"}, "ui-analysis"),
        ]),
        AgentTurnResult(FINAL_RESPONSE, text="Te he abierto el escandallo y este es el análisis solicitado."),
    ])
    result = HostAIAgent(
        engine, executor, HostAIToolCatalog.for_general_agent(registry),
    ).run("Ábreme el escandallo y dime por qué sale tan caro.")

    assert result.executed_tools == ["consultar_escandallos", "abrir_elaboracion"]
    assert result.ui_actions[0]["view"] == "ESCANDALLO"
    assert "análisis" in result.text


def test_policy_rechaza_vista_extra_url_y_propiedades_arbitrarias() -> None:
    tools = HostAIToolCatalog.for_general_agent(build_default_tool_registry()).effective_tools()
    policy = HostAIAgentPolicy()
    assert policy.authorize("abrir_elaboracion", {"elaboracion_id": "REC-1", "vista": "resumen"}, tools)[0] is False
    assert policy.authorize("abrir_elaboracion", {"url": "javascript:alert(1)"}, tools)[0] is False
    assert policy.authorize("abrir_elaboracion", {"elaboracion_id": "../../admin", "vista": "receta", "url": "/admin"}, tools)[0] is False
    assert policy.authorize("abrir_elaboracion", {"elaboracion_id": "REC-1"}, tools)[0] is False
    assert policy.authorize("crear_receta", {}, tools)[0] is False


def test_executor_rechaza_id_inexistente_y_accion_no_permitida() -> None:
    executor = HostAIToolExecutor(build_default_tool_registry(), escandallos_read_service=_Escandallos())
    missing = executor.execute_agent_ui_action("abrir_elaboracion", {
        "elaboracion_id": "REC-NO-EXISTE", "vista": "receta",
    })
    traversal = executor.execute_agent_ui_action("abrir_elaboracion", {
        "elaboracion_id": "../../admin", "vista": "receta",
    })
    unknown = executor.execute_agent_ui_action("abrir_url", {"url": "javascript:alert(1)"})
    assert missing.estado == traversal.estado == unknown.estado == "ERROR"
    assert missing.acciones == traversal.acciones == unknown.acciones == []


def test_shell_expone_evento_saneado_y_actualiza_contexto_sin_write(monkeypatch) -> None:
    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()))
    shell.agent_observability = SimpleNamespace(emit=lambda *_args, **_kwargs: None)
    monkeypatch.setattr(shell.general_agent, "run", lambda *_args, **_kwargs: AgentRunResult(
        True, "Te he abierto la receta.", "HAA-UI", "FAKE", "fake-model", 1,
        ["abrir_elaboracion"], ui_actions=[{
            "type": "OPEN_VIEW", "target": "ELABORACION", "id": "REC-ENSALADILLA",
            "view": "RECETA", "label": "Ensaladilla de gamba", "url": "javascript:alert(1)",
        }],
    ))

    response = shell.enviar("Enséñame la receta de la ensaladilla.", {"_host_ai_request_id": "HTTP-UI"})

    action = response["datos"]["ui_action"]
    assert action == {
        "type": "OPEN_VIEW", "target": "ELABORACION", "id": "REC-ENSALADILLA",
        "view": "RECETA", "label": "Ensaladilla de gamba", "safe": True,
        "datos_reales_modificados": False,
    }
    assert shell.estado_sesion()["receta_activa"]["id"] == "REC-ENSALADILLA"
    assert shell.estado_sesion()["receta_activa"]["tipo"] == "RECETA"
    assert shell.estado_sesion()["escandallo_activo"] == {}
    assert response["datos"]["datos_reales_modificados"] is False


def test_follow_up_recibe_identidad_activa_verificada(monkeypatch) -> None:
    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()))
    shell.agent_observability = SimpleNamespace(emit=lambda *_args, **_kwargs: None)
    captured = []

    def fake_run(_message, conversation_context=None):
        captured.append(deepcopy(conversation_context or {}))
        return AgentRunResult(True, "Respuesta.", "HAA-FOLLOW", "FAKE", "fake-model", 1, [])

    monkeypatch.setattr(shell.general_agent, "run", fake_run)
    shell._session.receta_activa = {"id": "REC-ENSALADILLA", "nombre": "Ensaladilla de gamba", "vista": "RECETA"}
    shell.enviar("¿Por qué sale tan cara?", {"_host_ai_request_id": "HTTP-FOLLOW"})

    assert captured[0]["active_entity"]["id"] == "REC-ENSALADILLA"
