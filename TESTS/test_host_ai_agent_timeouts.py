from __future__ import annotations

from types import SimpleNamespace

import SERVICIOS.host_ai_agent as agent_module
from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall
from SERVICIOS.host_ai_agent_policy import HostAIAgentPolicy
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog
from SERVICIOS.host_ai_tool_registry import build_default_tool_registry


class Clock:
    def __init__(self, values): self.values = iter(values); self.last = 0.0
    def __call__(self):
        try: self.last = next(self.values)
        except StopIteration: pass
        return self.last


class Engine:
    def __init__(self, turns): self.turns = list(turns); self.requests = []
    def ejecutar_turn_agente(self, request): self.requests.append(request); return self.turns.pop(0)


class Executor:
    def execute_agent_read(self, *_args): return SimpleNamespace(estado="OK", datos={"resultados": []})


def _agent(engine, policy=None):
    return HostAIAgent(engine, Executor(), HostAIToolCatalog(build_default_tool_registry()), policy)


def test_defaults_y_env_validada(monkeypatch):
    monkeypatch.delenv("HOST_AI_AGENT_PROVIDER_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("HOST_AI_AGENT_TOTAL_TIMEOUT_SECONDS", raising=False)
    assert HostAIAgentPolicy().PROVIDER_TIMEOUT_SECONDS == 60
    assert HostAIAgentPolicy().TOTAL_TIMEOUT_SECONDS == 90
    monkeypatch.setenv("HOST_AI_AGENT_PROVIDER_TIMEOUT_SECONDS", "75")
    monkeypatch.setenv("HOST_AI_AGENT_TOTAL_TIMEOUT_SECONDS", "120")
    assert HostAIAgentPolicy().PROVIDER_TIMEOUT_SECONDS == 75
    assert HostAIAgentPolicy().TOTAL_TIMEOUT_SECONDS == 120
    for invalid in ["x", "-1", "9999"]:
        monkeypatch.setenv("HOST_AI_AGENT_PROVIDER_TIMEOUT_SECONDS", invalid)
        monkeypatch.setenv("HOST_AI_AGENT_TOTAL_TIMEOUT_SECONDS", invalid)
        assert HostAIAgentPolicy().PROVIDER_TIMEOUT_SECONDS == 60
        assert HostAIAgentPolicy().TOTAL_TIMEOUT_SECONDS == 90


def test_segundo_turno_simulado_35s_cabe_en_presupuesto(monkeypatch):
    engine = Engine([
        AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_estado_stock", {}, "c1")]),
        AgentTurnResult(FINAL_RESPONSE, text="Final"),
    ])
    monkeypatch.setattr(agent_module.time, "perf_counter", Clock([0, 9, 9, 44, 44]))
    result = _agent(engine).run("consulta")
    assert result.ok and result.text == "Final"
    assert engine.requests[0].provider_timeout_seconds == 60
    assert engine.requests[1].provider_timeout_seconds == 60


def test_remaining_time_limita_timeout_provider(monkeypatch):
    engine = Engine([AgentTurnResult(FINAL_RESPONSE, text="Final")])
    policy = HostAIAgentPolicy(); policy.TOTAL_TIMEOUT_SECONDS = 50; policy.PROVIDER_TIMEOUT_SECONDS = 60
    monkeypatch.setattr(agent_module.time, "perf_counter", Clock([0, 15, 15]))
    assert _agent(engine, policy).run("consulta").ok
    assert engine.requests[0].provider_timeout_seconds == 35
    assert engine.requests[0].remaining_ms == 35000


def test_total_expirado_no_inicia_otro_turno(monkeypatch):
    engine = Engine([AgentTurnResult(TOOL_CALL, tool_calls=[ToolCall("consultar_estado_stock", {}, "c1")])])
    policy = HostAIAgentPolicy(); policy.TOTAL_TIMEOUT_SECONDS = 10
    monkeypatch.setattr(agent_module.time, "perf_counter", Clock([0, 1, 11]))
    result = _agent(engine, policy).run("consulta")
    assert not result.ok and result.safe_error == "agent_timeout"
    assert len(engine.requests) == 1
