from types import SimpleNamespace
import pytest
from API.contracts.http_models import validate_chat_payload

from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.reservas_read_service import ReservasReadService
from SERVICIOS.reservas_write_service import ReservasWriteService
from SERVICIOS.repositorio_reservas import RepositorioReservas
from MODELOS.reserva import Reserva


BASE = {"nombre_cliente": "Marta", "fecha": "2030-05-20", "hora": "21:00", "pax": 4, "servicio": "CENA"}
MINIMAL_REAL_CALL = {"nombre_cliente": "Marta", "fecha": "2030-05-20", "hora": "21:00", "pax": 4}


class Engine:
    def __init__(self, *turns): self.turns = list(turns); self.requests = []
    def ejecutar_turn_agente(self, request): self.requests.append(request); return self.turns.pop(0)


class Telemetry:
    def __init__(self): self.events = []
    def emit(self, event_type, **metadata): self.events.append({"event_type": event_type, **metadata})


def test_shell_local_completo_usa_identidad_interna_estable_para_confirmar(monkeypatch):
    for name in ("HOST_AI_INTERNAL_USER_ID", "HOST_AI_INTERNAL_TENANT_ID", "HOST_AI_INTERNAL_SCOPES"):
        monkeypatch.delenv(name, raising=False)
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()), session_id="same-session")
    context = shell.tool_executor.write_context
    assert context.user_id == "host-ai-local" and context.tenant_id == "host-ai-local"
    assert {"reservas:preview", "reservas:write"} <= context.scopes


def setup_agent(path, session, *turns):
    registry = build_default_tool_registry()
    context = AuthorizedExecutionContext("REQ", "chef", "restaurante", ("chat",), frozenset({"reservas:write"}))
    executor = HostAIToolExecutor(registry, reservas_read_service=ReservasReadService(path), reservas_write_service=ReservasWriteService(path), write_context=context, session_id=session)
    return HostAIAgent(Engine(*turns), executor, HostAIToolCatalog.for_general_agent(registry))


def test_runtime_real_shape_crear_reserva_prepara_preview_sin_persistir(tmp_path):
    agent = setup_agent(
        tmp_path, "runtime-real",
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("crear_reserva", MINIMAL_REAL_CALL, "real")]),
        AgentTurnResult(FINAL_RESPONSE, text="He preparado esta reserva. ¿Confirmas?"),
    )
    result = agent.run("Crea una reserva mañana a las 21:00 para 4 personas a nombre de Marta.")
    assert result.ok and result.executed_tools == ["crear_reserva"]
    assert result.datos_reales_modificados is False
    assert ReservasReadService(tmp_path).listar() == []
    pending = result.context_updates["confirmacion_reserva_pendiente"]
    assert pending["preview_token"] and pending["operacion"] == "CREAR"
    preview = agent.executor.reservas_write_service._pending[pending["preview_token"]]["payload"]
    assert preview["servicio"] == "CENA" and preview["estado"] == "PENDIENTE"


def test_runtime_local_sin_credenciales_solo_autoriza_preview(tmp_path):
    registry = build_default_tool_registry()
    empty_context = AuthorizedExecutionContext("chat-session", "", "", ("chat",), frozenset())
    executor = HostAIToolExecutor(
        registry, reservas_read_service=ReservasReadService(tmp_path),
        reservas_write_service=ReservasWriteService(tmp_path), write_context=empty_context,
        session_id="runtime-local",
    )
    preview = executor.execute_agent_write_flow("crear_reserva", MINIMAL_REAL_CALL, request_id="HTTP-REAL")
    assert preview.estado == "OK"
    assert preview.datos["datos_reales_modificados"] is False
    assert ReservasReadService(tmp_path).listar() == []
    token = preview.contexto_actualizado["confirmacion_reserva_pendiente"]["preview_token"]
    confirmation = executor.execute_agent_write_flow("aplicar_operacion_reserva", {"preview_token": token}, request_id="HTTP-CONFIRM")
    assert confirmation.estado == "ERROR" and confirmation.errores == ["unauthorized"]
    assert ReservasReadService(tmp_path).listar() == []


def test_error_semantico_preview_es_recuperable_y_conserva_motivo(tmp_path):
    agent = setup_agent(
        tmp_path, "retry",
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("crear_reserva", {**MINIMAL_REAL_CALL, "hora": "25:00"}, "bad")]),
        AgentTurnResult(FINAL_RESPONSE, text="Necesito una hora válida en formato HH:MM."),
    )
    telemetry = Telemetry()
    result = agent.run("Crea una reserva a las 25:00", conversation_context={"telemetry": telemetry, "request_id": "HTTP-R4"})
    assert result.ok and result.executed_tools == []
    assert result.datos_reales_modificados is False and ReservasReadService(tmp_path).listar() == []
    event = next(item for item in telemetry.events if item["event_type"] == "agent_tool_call")
    assert event["tool_id"] == "crear_reserva"
    assert event["authorized"] is True and event["executed"] is False
    assert event["rejection_reason"] == "invalid_reserva"
    assert event["tool_call_disposition"] == "REJECTED_EXECUTION"


def test_chat_crear_preview_no_persistir_y_si_confirma(tmp_path):
    preview_agent = setup_agent(tmp_path, "s1", AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("crear_reserva", BASE, "p")]), AgentTurnResult(FINAL_RESPONSE, text="He preparado la reserva. ¿Confirmas?"))
    preview = preview_agent.run("Crea una reserva para Marta")
    assert preview.ok and preview.executed_tools == ["crear_reserva"]
    assert preview.datos_reales_modificados is False and ReservasReadService(tmp_path).listar() == []
    pending = preview.context_updates["confirmacion_reserva_pendiente"]
    confirm_agent = HostAIAgent(Engine(AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("aplicar_operacion_reserva", {}, "c")]), AgentTurnResult(FINAL_RESPONSE, text="Reserva creada.")), preview_agent.executor, preview_agent.catalog)
    confirmed = confirm_agent.run("Sí.", conversation_context={"pending_confirmation": pending})
    assert confirmed.ok and confirmed.executed_tools == ["aplicar_operacion_reserva"]
    assert confirmed.datos_reales_modificados is True and len(ReservasReadService(tmp_path).listar()) == 1


def test_si_confirma_con_punto_aplica_una_vez_limpia_pending_y_audita(tmp_path):
    preview_agent = setup_agent(tmp_path, "same-session", AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("crear_reserva", MINIMAL_REAL_CALL, "p")]), AgentTurnResult(FINAL_RESPONSE, text="¿Confirmas?"))
    preview = preview_agent.run("Crea una reserva")
    pending = preview.context_updates["confirmacion_reserva_pendiente"]
    telemetry = Telemetry()
    confirm_agent = HostAIAgent(
        Engine(AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("aplicar_operacion_reserva", {}, "c")]), AgentTurnResult(FINAL_RESPONSE, text="Reserva creada.")),
        preview_agent.executor, preview_agent.catalog,
    )
    confirmed = confirm_agent.run("Sí, confirma.", conversation_context={"pending_confirmation": pending, "telemetry": telemetry, "request_id": "HTTP-CONFIRM"})
    assert confirmed.ok and confirmed.executed_tools == ["aplicar_operacion_reserva"]
    assert confirmed.datos_reales_modificados is True
    assert confirmed.context_updates["confirmacion_reserva_pendiente"] == {}
    stored = ReservasReadService(tmp_path).listar()
    assert len(stored) == 1 and stored[0]["reserva_id"] == preview_agent.executor.reservas_write_service._completed[pending["preview_token"]]["result"]["reserva"]["reserva_id"]
    event_types = [item["event_type"] for item in telemetry.events]
    assert "confirmation_explicit" in event_types and "confirmation_applied" in event_types

    replay = preview_agent.executor.execute_agent_write_flow("aplicar_operacion_reserva", {"preview_token": pending["preview_token"]}, request_id="HTTP-REPLAY")
    assert replay.estado == "OK" and replay.datos["idempotente"] is True
    assert len(ReservasReadService(tmp_path).listar()) == 1


def test_confirmacion_ambigua_o_sin_pending_no_escribe_y_emite_missing(tmp_path):
    telemetry = Telemetry()
    agent = setup_agent(
        tmp_path, "no-pending",
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("aplicar_operacion_reserva", {"preview_token": "inventado"}, "c")]),
        AgentTurnResult(FINAL_RESPONSE, text="No hay una confirmación pendiente."),
    )
    result = agent.run("Sí, quizá.", conversation_context={"telemetry": telemetry, "request_id": "HTTP-MISSING"})
    assert result.ok and result.datos_reales_modificados is False
    assert ReservasReadService(tmp_path).listar() == []
    assert any(item["event_type"] == "confirmation_missing" and item["reason"] == "confirmation_missing" for item in telemetry.events)


def test_chat_no_confirma_sin_si_explicito_ni_preview_y_aisla_sesion(tmp_path):
    preview_agent = setup_agent(tmp_path, "s1", AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("crear_reserva", BASE, "p")]), AgentTurnResult(FINAL_RESPONSE, text="Preview"))
    pending = preview_agent.run("prepara").context_updates["confirmacion_reserva_pendiente"]
    no = HostAIAgent(Engine(AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("aplicar_operacion_reserva", {"preview_token": pending["preview_token"]}, "c")]), AgentTurnResult(FINAL_RESPONSE, text="No aplicado")), preview_agent.executor, preview_agent.catalog).run("todavía no")
    assert no.datos_reales_modificados is False and ReservasReadService(tmp_path).listar() == []
    other = setup_agent(tmp_path, "s2", AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("aplicar_operacion_reserva", {"preview_token": pending["preview_token"]}, "x")]))
    failed = other.run("Sí.", conversation_context={"pending_confirmation": pending})
    assert failed.ok is False and ReservasReadService(tmp_path).listar() == []


def test_chat_cancelar_requiere_dos_turnos_y_crear_otra_no_replay(tmp_path):
    creator = setup_agent(tmp_path, "s1", AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("crear_reserva", BASE, "p")]), AgentTurnResult(FINAL_RESPONSE, text="Preview"))
    first = creator.run("crea")
    confirmer = HostAIAgent(Engine(AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("aplicar_operacion_reserva", {}, "c")]), AgentTurnResult(FINAL_RESPONSE, text="Creada")), creator.executor, creator.catalog)
    created = confirmer.run("Sí", conversation_context={"pending_confirmation": first.context_updates["confirmacion_reserva_pendiente"]})
    reservation_id = created.context_updates["reserva_activa"]["reserva_id"]
    cancel = HostAIAgent(Engine(AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("cancelar_reserva", {"reserva_id": reservation_id}, "pc")]), AgentTurnResult(FINAL_RESPONSE, text="¿Confirmas cancelación?")), creator.executor, creator.catalog).run("Cancélala")
    assert ReservasReadService(tmp_path).detalle(reservation_id)["estado"] == "PENDIENTE"
    applied = HostAIAgent(Engine(AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("aplicar_operacion_reserva", {}, "cc")]), AgentTurnResult(FINAL_RESPONSE, text="Cancelada")), creator.executor, creator.catalog).run("Sí", conversation_context={"pending_confirmation": cancel.context_updates["confirmacion_reserva_pendiente"]})
    assert applied.context_updates["reserva_activa"]["estado"] == "CANCELADA"
    another = creator.executor.execute_agent_write_flow("crear_reserva", BASE, request_id="REQ-2")
    assert another.contexto_actualizado["confirmacion_reserva_pendiente"]["preview_token"] != first.context_updates["confirmacion_reserva_pendiente"]["preview_token"]


@pytest.mark.parametrize("confirmation", ["Sí, confirmar cancelación.", "Confirmo.", "Sí, cancélala."])
def test_confirmacion_semantica_cancelacion_aplica_y_limpia_pending(tmp_path, confirmation):
    creator = setup_agent(tmp_path, "cancel-session", AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("crear_reserva", BASE, "p")]), AgentTurnResult(FINAL_RESPONSE, text="Preview"))
    created_preview = creator.run("crea")
    created = creator.executor.execute_agent_write_flow(
        "aplicar_operacion_reserva",
        {"preview_token": created_preview.context_updates["confirmacion_reserva_pendiente"]["preview_token"]},
        request_id="CREATE",
    )
    reserva_id = created.datos["reserva"]["reserva_id"]
    cancel_preview = creator.executor.execute_agent_write_flow("cancelar_reserva", {"reserva_id": reserva_id}, request_id="CANCEL-PREVIEW")
    pending = cancel_preview.contexto_actualizado["confirmacion_reserva_pendiente"]
    telemetry = Telemetry()
    confirmer = HostAIAgent(
        Engine(AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("aplicar_operacion_reserva", {}, "confirm")]), AgentTurnResult(FINAL_RESPONSE, text="Reserva cancelada.")),
        creator.executor, creator.catalog,
    )
    result = confirmer.run(confirmation, conversation_context={"pending_confirmation": pending, "telemetry": telemetry, "request_id": "HTTP-CANCEL"})
    assert result.ok and result.datos_reales_modificados is True
    assert result.context_updates["confirmacion_reserva_pendiente"] == {}
    stored = ReservasReadService(tmp_path).listar()
    assert len(stored) == 1 and stored[0]["reserva_id"] == reserva_id and stored[0]["estado"] == "CANCELADA"
    events = [item["event_type"] for item in telemetry.events]
    assert "confirmation_explicit" in events and "confirmation_applied" in events
    assert "confirmation_missing" not in events


@pytest.mark.parametrize("message", ["no", "mantener", "quizá", "luego", "¿confirmar?"])
def test_cancelacion_rechaza_texto_no_inequivoco(tmp_path, message):
    creator = setup_agent(tmp_path, "reject-session", AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("crear_reserva", BASE, "p")]), AgentTurnResult(FINAL_RESPONSE, text="Preview"))
    created_preview = creator.run("crea")
    created = creator.executor.execute_agent_write_flow("aplicar_operacion_reserva", {"preview_token": created_preview.context_updates["confirmacion_reserva_pendiente"]["preview_token"]}, request_id="CREATE")
    reserva_id = created.datos["reserva"]["reserva_id"]
    cancel_preview = creator.executor.execute_agent_write_flow("cancelar_reserva", {"reserva_id": reserva_id}, request_id="CANCEL-PREVIEW")
    pending = cancel_preview.contexto_actualizado["confirmacion_reserva_pendiente"]
    agent = HostAIAgent(
        Engine(AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("aplicar_operacion_reserva", {}, "confirm")]), AgentTurnResult(FINAL_RESPONSE, text="No aplicada.")),
        creator.executor, creator.catalog,
    )
    result = agent.run(message, conversation_context={"pending_confirmation": pending})
    assert result.datos_reales_modificados is False
    assert ReservasReadService(tmp_path).detalle(reserva_id)["estado"] == "PENDIENTE"


def test_chat_modificar_cancelada_rechaza_grounded_sin_preview_ni_confirmacion(tmp_path):
    creator = setup_agent(tmp_path, "terminal-chat", AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("crear_reserva", BASE, "create")]), AgentTurnResult(FINAL_RESPONSE, text="Preview"))
    create_preview = creator.run("crea")
    created = creator.executor.execute_agent_write_flow("aplicar_operacion_reserva", {"preview_token": create_preview.context_updates["confirmacion_reserva_pendiente"]["preview_token"]}, request_id="CREATE")
    reserva_id = created.datos["reserva"]["reserva_id"]
    cancel_preview = creator.executor.execute_agent_write_flow("cancelar_reserva", {"reserva_id": reserva_id}, request_id="CANCEL")
    creator.executor.execute_agent_write_flow("aplicar_operacion_reserva", {"preview_token": cancel_preview.contexto_actualizado["confirmacion_reserva_pendiente"]["preview_token"]}, request_id="APPLY-CANCEL")
    pending_before = set(creator.executor.reservas_write_service._pending)
    agent = HostAIAgent(
        Engine(
            AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("modificar_reserva", {"reserva_id": reserva_id, "hora": "22:00"}, "modify")]),
            AgentTurnResult(FINAL_RESPONSE, text="La reserva está CANCELADA y no puede modificarse."),
        ), creator.executor, creator.catalog,
    )
    result = agent.run(f"Cambia la reserva {reserva_id} a las 22:00")
    assert result.ok and result.executed_tools == []
    assert "CANCELADA" in result.text and "no puede modificarse" in result.text
    assert "confirmacion_reserva_pendiente" not in result.context_updates
    assert set(creator.executor.reservas_write_service._pending) == pending_before
    stored = ReservasReadService(tmp_path).detalle(reserva_id)
    assert stored["estado"] == "CANCELADA" and stored["hora"] == "21:00"


@pytest.mark.parametrize("state", ["CANCELADA", "NO_SHOW", "COMPLETADA"])
def test_capability_awareness_terminal_es_read_only_y_solo_ofrece_alternativas_validas(tmp_path, state):
    reserva_id = "RES-AAAAAAAAAAAA"
    RepositorioReservas(tmp_path).guardar_todos([Reserva.crear(reserva_id=reserva_id, **BASE, estado=state)])
    engine = Engine(
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("modificar_reserva", {"reserva_id": reserva_id, "hora": "22:00"}, "modify")]),
        AgentTurnResult(FINAL_RESPONSE, text="También puedo añadir una observación o cancelarla."),
    )
    registry = build_default_tool_registry()
    context = AuthorizedExecutionContext("REQ", "chef", "restaurante", ("chat",), frozenset({"reservas:write"}))
    executor = HostAIToolExecutor(registry, reservas_read_service=ReservasReadService(tmp_path), reservas_write_service=ReservasWriteService(tmp_path), write_context=context, session_id="terminal")
    result = HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(registry)).run(f"Cambia la reserva {reserva_id} a las 22:00")
    lowered = result.text.lower()
    assert state.lower() in lowered and "solo lectura" in lowered
    assert "abrir su ficha" in lowered and "nueva reserva" in lowered
    assert all(value not in lowered for value in ("añadir", "observación", "cancelarla", "confirmarla", "completarla"))
    tool_message = next(message for message in engine.requests[1].messages if message.get("role") == "tool")
    capabilities = tool_message["content"]["reservation_capabilities"]
    assert capabilities["read_only"] is True and capabilities["estado"] == state
    assert result.datos_reales_modificados is False and ReservasReadService(tmp_path).detalle(reserva_id)["hora"] == "21:00"


@pytest.mark.parametrize(("state", "required", "forbidden"), [
    ("PENDIENTE", ("modificar", "confirmar", "cancelar"), ("no-show", "completar")),
    ("CONFIRMADA", ("modificar", "cancelar", "no-show", "completar"), ("volver a confirmar", "notificacion al cliente")),
])
def test_contexto_activo_comunica_solo_capacidades_validas_no_terminales(tmp_path, state, required, forbidden):
    engine = Engine(AgentTurnResult(FINAL_RESPONSE, text="Información de capacidades."))
    registry = build_default_tool_registry()
    executor = HostAIToolExecutor(registry, reservas_read_service=ReservasReadService(tmp_path))
    HostAIAgent(engine, executor, HostAIToolCatalog.for_general_agent(registry)).run(
        "¿Qué puedo hacer?", conversation_context={"active_entity": {"tipo": "RESERVA", "reserva_id": "RES-AAAAAAAAAAAA", "estado": state}}
    )
    developer = " ".join(str(message.get("content") or "") for message in engine.requests[0].messages if message.get("role") == "developer").lower()
    assert all(value in developer for value in required)
    assert all(value in developer for value in forbidden)


def test_chat_completar_confirmada_preview_confirma_y_queda_terminal(tmp_path):
    reserva_id = "RES-AAAAAAAAAAAA"
    RepositorioReservas(tmp_path).guardar_todos([Reserva.crear(reserva_id=reserva_id, **BASE, estado="CONFIRMADA")])
    agent = setup_agent(tmp_path, "complete-session", AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("completar_reserva", {"reserva_id": reserva_id}, "preview")]), AgentTurnResult(FINAL_RESPONSE, text="He preparado completar la reserva. ¿Confirmas?"))
    preview = agent.run(f"Marca la reserva {reserva_id} como completada")
    assert preview.ok and preview.executed_tools == ["completar_reserva"]
    assert ReservasReadService(tmp_path).detalle(reserva_id)["estado"] == "CONFIRMADA"
    pending = preview.context_updates["confirmacion_reserva_pendiente"]
    assert pending["operacion"] == "COMPLETAR"
    confirmer = HostAIAgent(Engine(AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("aplicar_operacion_reserva", {}, "apply")]), AgentTurnResult(FINAL_RESPONSE, text="Reserva completada.")), agent.executor, agent.catalog)
    result = confirmer.run("Sí, confirmar.", conversation_context={"pending_confirmation": pending})
    assert result.datos_reales_modificados is True
    assert ReservasReadService(tmp_path).detalle(reserva_id)["estado"] == "COMPLETADA"
    assert agent.executor.execute_agent_write_flow("modificar_reserva", {"reserva_id": reserva_id, "hora": "22:00"}, request_id="BLOCK").errores == ["terminal_state"]


def test_shell_preview_publica_acciones_y_aplicar_usa_pending_sin_token_cliente(tmp_path, monkeypatch):
    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    preview_agent = setup_agent(tmp_path, "button-session", AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("crear_reserva", MINIMAL_REAL_CALL, "preview")]), AgentTurnResult(FINAL_RESPONSE, text="Preview listo."))
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()), session_id="button-session")
    shell.tool_executor = preview_agent.executor; shell.general_agent = preview_agent
    preview_response = shell.enviar("Crea una reserva", contexto={"_host_ai_request_id": "HTTP-PREVIEW"})
    assert preview_response["mensaje"] == "He preparado el cambio. Revisa los datos y elige una opcion."
    assert "confirmar" not in preview_response["mensaje"].lower()
    actions = preview_response["datos"]["confirmation_actions"]
    assert [item["action_id"] for item in actions] == ["APPLY_PENDING_RESERVATION", "DISCARD_PENDING_RESERVATION"]
    assert all("token" not in str(item).lower() and "reserva_id" not in item for item in actions)
    assert ReservasReadService(tmp_path).listar() == []
    shell.general_agent = HostAIAgent(Engine(AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("aplicar_operacion_reserva", {}, "apply")]), AgentTurnResult(FINAL_RESPONSE, text="Reserva creada.")), preview_agent.executor, preview_agent.catalog)
    applied = shell.ejecutar_accion_reserva("APPLY_PENDING_RESERVATION", contexto={"_host_ai_request_id": "HTTP-APPLY"})
    assert [item["action_id"] for item in applied["datos"]["confirmation_actions"]] == ["CONFIRM_RESERVATION", "EDIT_RESERVATION", "CANCEL_RESERVATION", "OPEN_RESERVATION"]
    assert applied["datos"]["datos_reales_modificados"] is True
    assert len(ReservasReadService(tmp_path).listar()) == 1
    replay = shell.ejecutar_accion_reserva("APPLY_PENDING_RESERVATION")
    assert replay["datos"]["datos_reales_modificados"] is False and len(ReservasReadService(tmp_path).listar()) == 1


def test_descartar_accion_limpia_pending_y_no_permite_confirmar_despues(tmp_path, monkeypatch):
    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    preview_agent = setup_agent(tmp_path, "discard-session", AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("crear_reserva", MINIMAL_REAL_CALL, "preview")]), AgentTurnResult(FINAL_RESPONSE, text="Preview listo."))
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()), session_id="discard-session")
    shell.tool_executor = preview_agent.executor; shell.general_agent = preview_agent
    shell.enviar("Crea una reserva", contexto={"_host_ai_request_id": "HTTP-PREVIEW"})
    discarded = shell.ejecutar_accion_reserva("DISCARD_PENDING_RESERVATION")
    assert discarded["datos"]["confirmation_actions"] == [] and shell._session.confirmacion_reserva_pendiente == {}
    assert ReservasReadService(tmp_path).listar() == []
    after = shell.ejecutar_accion_reserva("APPLY_PENDING_RESERVATION")
    assert after["datos"]["datos_reales_modificados"] is False and ReservasReadService(tmp_path).listar() == []


def test_action_id_chat_es_cerrado_y_no_acepta_payload_arbitrario():
    assert validate_chat_payload({"mensaje": "", "action_id": "APPLY_PENDING_RESERVATION", "contexto": {"session_id": "s1"}}) == (True, "")
    assert validate_chat_payload({"mensaje": "", "action_id": "https://evil.test", "contexto": {"session_id": "s1"}}) == (False, "invalid_action_id")
    assert validate_chat_payload({"mensaje": "", "action_id": "APPLY_PENDING_RESERVATION", "preview_token": "fake"}) == (False, "unknown_fields")
    assert validate_chat_payload({"mensaje": "", "action_id": "CONFIRM_RESERVATION"}) == (False, "action_context_required")
    assert validate_chat_payload({"mensaje": "", "action_id": "CONFIRM_RESERVATION", "action_context_id": "a" * 32}) == (True, "")
    assert validate_chat_payload({"mensaje": "", "action_id": "CONFIRM_RESERVATION", "action_context_id": "../../reserva"}) == (False, "invalid_action_context_id")


def contextual_shell(tmp_path, state="PENDIENTE", session="contextual"):
    reserva_id = "RES-AAAAAAAAAAAA"
    RepositorioReservas(tmp_path).guardar_todos([Reserva.crear(reserva_id=reserva_id, **BASE, estado=state)])
    agent = setup_agent(tmp_path, session, AgentTurnResult(FINAL_RESPONSE, text="unused"))
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()), session_id=session)
    shell.tool_executor = agent.executor
    shell._session.reserva_activa = dict(ReservasReadService(tmp_path).detalle(reserva_id))
    return shell, reserva_id


@pytest.mark.parametrize(("state", "expected"), [
    ("PENDIENTE", ["CONFIRM_RESERVATION", "EDIT_RESERVATION", "CANCEL_RESERVATION", "OPEN_RESERVATION"]),
    ("CONFIRMADA", ["EDIT_RESERVATION", "CANCEL_RESERVATION", "MARK_RESERVATION_NO_SHOW", "COMPLETE_RESERVATION", "OPEN_RESERVATION"]),
    ("CANCELADA", ["OPEN_RESERVATION"]), ("NO_SHOW", ["OPEN_RESERVATION"]), ("COMPLETADA", ["OPEN_RESERVATION"]),
])
def test_acciones_contextuales_reflejan_estado_real(tmp_path, state, expected):
    shell, _ = contextual_shell(tmp_path, state)
    actions = shell._reservation_actions()
    assert [item["action_id"] for item in actions] == expected
    assert all("token" not in str(item).lower() and "reserva_id" not in item for item in actions)


@pytest.mark.parametrize(("state", "action", "operation"), [
    ("PENDIENTE", "CONFIRM_RESERVATION", "CONFIRMAR"),
    ("PENDIENTE", "CANCEL_RESERVATION", "CANCELAR"),
    ("CONFIRMADA", "MARK_RESERVATION_NO_SHOW", "NO_SHOW"),
    ("CONFIRMADA", "COMPLETE_RESERVATION", "COMPLETAR"),
])
def test_accion_contextual_inicia_preview_sin_write(tmp_path, state, action, operation):
    shell, reserva_id = contextual_shell(tmp_path, state)
    before = ReservasReadService(tmp_path).detalle(reserva_id)
    shell._reservation_actions()
    context_id = shell._session.acciones_reserva_contextuales["context_id"]
    result = shell.ejecutar_accion_reserva(action, action_context_id=context_id)
    assert result["datos"]["preview"]["operacion"] == operation
    assert [item["action_id"] for item in result["datos"]["reservation_actions"]] == ["APPLY_PENDING_RESERVATION", "DISCARD_PENDING_RESERVATION"]
    assert ReservasReadService(tmp_path).detalle(reserva_id) == before
    assert result["datos"]["datos_reales_modificados"] is False


def test_accion_contextual_revalida_stale_y_sesion(tmp_path):
    shell, reserva_id = contextual_shell(tmp_path, "PENDIENTE", "session-a")
    shell._reservation_actions()
    context_id = shell._session.acciones_reserva_contextuales["context_id"]
    current = Reserva.from_dict(ReservasReadService(tmp_path).detalle(reserva_id))
    RepositorioReservas(tmp_path).guardar_todos([Reserva.from_dict({**current.to_dict(), "estado": "CONFIRMADA"})])
    stale = shell.ejecutar_accion_reserva("CONFIRM_RESERVATION", action_context_id=context_id)
    assert stale["datos"]["reason"] == "stale_reservation_action"
    assert shell._session.confirmacion_reserva_pendiente == {}
    other = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=object()), session_id="session-b")
    other.tool_executor = shell.tool_executor
    other._session.reserva_activa = {"reserva_id": reserva_id, "estado": "CONFIRMADA"}
    rejected = other.ejecutar_accion_reserva("COMPLETE_RESERVATION", action_context_id=context_id)
    assert rejected["datos"]["reason"] == "stale_reservation_action"
    assert ReservasReadService(tmp_path).detalle(reserva_id)["estado"] == "CONFIRMADA"


def test_boton_de_mensaje_anterior_no_puede_iniciar_preview(tmp_path):
    shell, _ = contextual_shell(tmp_path)
    shell._reservation_actions()
    old_context_id = shell._session.acciones_reserva_contextuales["context_id"]
    shell._reservation_actions()
    rejected = shell.ejecutar_accion_reserva("CONFIRM_RESERVATION", action_context_id=old_context_id)
    assert rejected["datos"]["reason"] == "stale_reservation_action"
    assert shell._session.confirmacion_reserva_pendiente == {}


@pytest.mark.parametrize("action", ["EDIT_RESERVATION", "OPEN_RESERVATION"])
def test_modificar_y_abrir_reutilizan_open_view_seguro(tmp_path, action):
    shell, reserva_id = contextual_shell(tmp_path)
    shell._reservation_actions()
    context_id = shell._session.acciones_reserva_contextuales["context_id"]
    result = shell.ejecutar_accion_reserva(action, action_context_id=context_id)
    assert result["datos"]["ui_action"] == {"type": "OPEN_VIEW", "target": "RESERVAS", "id": reserva_id, "view": "DETALLE", "label": reserva_id}
    assert result["datos"]["datos_reales_modificados"] is False
