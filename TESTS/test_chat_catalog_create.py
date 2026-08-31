from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.host_ai_tool_executor import HostAIToolExecutor
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry
from SERVICIOS.catalog_crud_write_service import CatalogCrudWriteService
from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.host_ai_engine.service import HostAIEngine


class Engine:
    def __init__(self, *turns): self.turns = list(turns)
    def ejecutar_turn_agente(self, request): return self.turns.pop(0)


def _executor(base: Path, session: str = "CHAT-1") -> HostAIToolExecutor:
    db = base / "DATOS/db"; db.mkdir(parents=True)
    (db / "eventos.json").write_text("[]", encoding="utf-8")
    (db / "articulos.json").write_text("[]", encoding="utf-8")
    context = AuthorizedExecutionContext("REQ", "chef", "local", ("chef",), frozenset({
        "eventos:preview", "eventos:write", "articulos:preview", "articulos:write",
        "recetas:preview", "recetas:write",
    }))
    return HostAIToolExecutor(build_default_tool_registry(), articulos_read_service=SimpleNamespace(base_dir=base), catalog_crud_service=CatalogCrudWriteService(base), write_context=context, session_id=session)


@pytest.mark.parametrize(("tool", "payload", "domain", "target"), [
    ("preparar_creacion_evento", {"nombre": "Boda", "fecha": "2030-09-12", "pax": 30}, "EVENTO", "EVENTOS"),
    ("preparar_creacion_articulo", {"nombre": "Aceite AOVE", "codigo": "ART-AOVE", "unidad_base": "kg"}, "ARTICULO", "ARTICULO"),
    ("preparar_creacion_receta", {"nombre": "Croquetas", "codigo": "REC-CROQ", "numero_raciones": 10, "ingredientes": ["Jamón"], "cantidades": ["200 g"], "ingredientes_estructurados": [{"nombre": "Jamón", "article_id": None, "estado": "SIN_VINCULAR"}], "elaboracion": "Mezclar y freír."}, "RECETA", "ELABORACION"),
])
def test_chat_catalog_create_is_preview_then_confirm_idempotent(tmp_path: Path, tool: str, payload: dict, domain: str, target: str) -> None:
    executor = _executor(tmp_path)
    preview = executor.execute_catalog_create_flow(tool, payload, "REQ-PREVIEW")
    assert preview.estado == "OK"
    assert preview.datos["datos_reales_modificados"] is False
    pending = preview.contexto_actualizado["confirmacion_catalogo_pendiente"]
    assert pending["dominio"] == domain and pending["session_id"] == "CHAT-1"
    confirmed = executor.execute_catalog_create_flow("aplicar_creacion_catalogo", {"preview_token": pending["preview_token"]}, "REQ-CONFIRM")
    repeated = executor.execute_catalog_create_flow("aplicar_creacion_catalogo", {"preview_token": pending["preview_token"]}, "REQ-CONFIRM")
    assert confirmed.datos["datos_reales_modificados"] is True
    assert confirmed.datos["ui_action"]["target"] == target
    assert repeated.datos["idempotente"] is True


def test_cancelled_and_missing_preview_never_write(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    preview = executor.execute_catalog_create_flow("preparar_creacion_evento", {"nombre": "Cena", "fecha": "2030-10-01", "pax": 8})
    token = preview.datos["preview_token"]
    discarded = executor.discard_catalog_create(token)
    assert discarded.datos["datos_reales_modificados"] is False
    refused = executor.execute_catalog_create_flow("aplicar_creacion_catalogo", {"preview_token": token})
    assert refused.estado == "ERROR"
    assert json.loads((tmp_path / "DATOS/db/eventos.json").read_text()) == []


def test_article_create_does_not_modify_stock_and_duplicate_is_rejected(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    stock = tmp_path / "DATOS/db/stock_movimientos.json"; stock.write_text("[]", encoding="utf-8")
    payload = {"nombre": "Aceite", "codigo": "ART-ACEITE", "unidad_base": "kg"}
    first = executor.execute_catalog_create_flow("preparar_creacion_articulo", payload)
    executor.execute_catalog_create_flow("aplicar_creacion_catalogo", {"preview_token": first.datos["preview_token"]})
    duplicate = executor.execute_catalog_create_flow("preparar_creacion_articulo", payload)
    assert duplicate.estado == "ERROR" and duplicate.errores == ["duplicate"]
    assert json.loads(stock.read_text()) == []


def test_agent_preview_then_explicit_confirmation_uses_pending_payload(tmp_path: Path) -> None:
    executor = _executor(tmp_path, "AGENT")
    registry = executor.registry
    payload = {"nombre": "Boda Marta", "fecha": "2030-09-12", "pax": 30, "cliente": "Marta"}
    preview_agent = HostAIAgent(Engine(AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("preparar_creacion_evento", payload, "p")]), AgentTurnResult(FINAL_RESPONSE, text="Revisa el evento.")), executor, HostAIToolCatalog.for_general_agent(registry))
    preview = preview_agent.run("Crea un evento para Marta")
    assert preview.executed_tools == ["preparar_creacion_evento"] and preview.datos_reales_modificados is False
    pending = preview.context_updates["confirmacion_catalogo_pendiente"]
    confirm_agent = HostAIAgent(Engine(AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("aplicar_creacion_catalogo", {}, "c")]), AgentTurnResult(FINAL_RESPONSE, text="Evento creado.")), executor, HostAIToolCatalog.for_general_agent(registry))
    confirmed = confirm_agent.run("Sí, confirmar.", conversation_context={"pending_confirmation": pending})
    assert confirmed.executed_tools == ["aplicar_creacion_catalogo"] and confirmed.datos_reales_modificados is True
    saved = json.loads((tmp_path / "DATOS/db/eventos.json").read_text())
    assert saved[0]["nombre"] == payload["nombre"] and saved[0]["pax"] == payload["pax"]


def test_incomplete_request_and_recipe_proposal_do_not_write(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    agent = HostAIAgent(Engine(AgentTurnResult(FINAL_RESPONSE, text="Necesito la fecha y el número de personas.")), executor, HostAIToolCatalog.for_general_agent(executor.registry))
    result = agent.run("Crea un evento para Marta")
    assert result.executed_tools == [] and json.loads((tmp_path / "DATOS/db/eventos.json").read_text()) == []
    recipe_agent = HostAIAgent(Engine(AgentTurnResult(FINAL_RESPONSE, text="Te propongo unas croquetas.")), executor, HostAIToolCatalog.for_general_agent(executor.registry))
    proposed = recipe_agent.run("Propón una receta de croquetas")
    assert proposed.executed_tools == [] and executor.catalog_crud_service.recipes.listar() == []


def test_recipe_proposal_is_reused_exactly_when_later_saved(tmp_path: Path) -> None:
    executor = _executor(tmp_path, "RECIPE-PROPOSAL")
    catalog = HostAIToolCatalog.for_general_agent(executor.registry)
    original = {
        "nombre": "Crema de calabaza", "codigo": "REC-CALABAZA", "numero_raciones": 6,
        "ingredientes": ["Calabaza", "Aceite"], "cantidades": ["900 g", "30 ml"],
        "ingredientes_estructurados": [
            {"nombre": "Calabaza", "article_id": None, "estado": "SIN_VINCULAR"},
            {"nombre": "Aceite", "article_id": None, "estado": "SIN_VINCULAR"},
        ],
        "elaboracion": "Asar, triturar y emulsionar.",
    }
    remember = HostAIAgent(Engine(
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("conservar_propuesta_receta", original, "remember")]),
        AgentTurnResult(FINAL_RESPONSE, text="Propuesta preparada."),
    ), executor, catalog).run("¿Puedes proponer una receta?")
    assert remember.datos_reales_modificados is False
    assert remember.context_updates["propuesta_receta_activa"] == original

    reconstructed = dict(original)
    reconstructed["cantidades"] = ["500 g", "10 ml"]
    preview = HostAIAgent(Engine(
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("preparar_creacion_receta", reconstructed, "preview")]),
        AgentTurnResult(FINAL_RESPONSE, text="Revisa la receta."),
    ), executor, catalog).run("¿Puedes guardarla?", conversation_context={"recipe_proposal": original})
    pending = preview.context_updates["confirmacion_catalogo_pendiente"]
    assert pending["payload"]["cantidades"] == original["cantidades"]
    assert pending["payload"]["ingredientes_estructurados"] == original["ingredientes_estructurados"]

    confirmed = HostAIAgent(Engine(
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("aplicar_creacion_catalogo", {}, "confirm")]),
        AgentTurnResult(FINAL_RESPONSE, text="Receta creada."),
    ), executor, catalog).run("Sí, confirmar", conversation_context={"pending_confirmation": pending})
    assert confirmed.context_updates["propuesta_receta_activa"] == {}
    saved = executor.catalog_crud_service.recipes.listar()[0]
    assert saved["cantidades"] == original["cantidades"]
    assert saved["ingredientes_estructurados"] == original["ingredientes_estructurados"]


def test_confirmation_uses_current_preview_not_an_older_model_token(tmp_path: Path) -> None:
    executor = _executor(tmp_path, "REPLACED")
    first = executor.execute_catalog_create_flow("preparar_creacion_evento", {"nombre": "Evento A", "fecha": "2030-01-01", "pax": 10})
    second = executor.execute_catalog_create_flow("preparar_creacion_evento", {"nombre": "Evento B", "fecha": "2030-01-02", "pax": 20})
    current = second.contexto_actualizado["confirmacion_catalogo_pendiente"]
    agent = HostAIAgent(Engine(
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("aplicar_creacion_catalogo", {"preview_token": first.datos["preview_token"]}, "confirm")]),
        AgentTurnResult(FINAL_RESPONSE, text="Evento creado."),
    ), executor, HostAIToolCatalog.for_general_agent(executor.registry))
    result = agent.run("Sí, confirmar", conversation_context={"pending_confirmation": current})
    assert result.datos_reales_modificados is True
    saved = json.loads((tmp_path / "DATOS/db/eventos.json").read_text())
    assert [item["nombre"] for item in saved] == ["Evento B"]


def test_expired_and_invalid_tokens_never_write(tmp_path: Path) -> None:
    clock = [datetime(2030, 1, 1, 10, 0, 0)]
    executor = _executor(tmp_path, "EXPIRY")
    executor.catalog_crud_service = CatalogCrudWriteService(tmp_path, now_provider=lambda: clock[0], ttl_seconds=30)
    preview = executor.execute_catalog_create_flow("preparar_creacion_evento", {"nombre": "Caducado", "fecha": "2030-02-01", "pax": 12})
    clock[0] += timedelta(seconds=31)
    expired = executor.execute_catalog_create_flow("aplicar_creacion_catalogo", {"preview_token": preview.datos["preview_token"]})
    invalid = executor.execute_catalog_create_flow("aplicar_creacion_catalogo", {"preview_token": "not-a-real-token"})
    assert expired.errores == ["expired_preview"]
    assert invalid.errores == ["invalid_preview"]
    assert json.loads((tmp_path / "DATOS/db/eventos.json").read_text()) == []


def test_simulated_route_promotes_event_to_structured_preview(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("HOST_AI_GENERAL_AGENT_READ", raising=False)
    shell = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=HostAIEngine(tmp_path)), session_id="REAL-SIM")
    shell._catalog_executor.catalog_crud_service = CatalogCrudWriteService(tmp_path)
    response = shell.enviar(
        "Crea un evento de prueba para mañana a las 18:00 para 20 personas. No lo guardes hasta que yo confirme.",
        {"_host_ai_request_id": "REQ-REAL-SIM"},
    )
    pending = response["datos"]["pending_write"]
    assert pending["domain"] == "EVENTO" and pending["operation"] == "CREAR"
    assert pending["preview"]["nombre"].lower() == "prueba"
    assert pending["preview"]["hora_inicio"] == "18:00" and pending["preview"]["pax"] == 20
    assert response["datos"]["datos_reales_modificados"] is False
    assert [item["label"] for item in response["datos"]["confirmation_actions"]] == ["Confirmar", "Cancelar"]
    assert "SIMULACION" not in response["mensaje"]
