from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from API.app import HostAIPlatformAPI
from API.contracts.http_models import ApiRequest
from SERVICIOS.host_ai_agent import HostAIAgent
from SERVICIOS.host_ai_agent_models import AgentRunResult, AgentTurnRequest
from SERVICIOS.host_ai_agent_observability import HostAIAgentObservability
from SERVICIOS.host_ai_engine.openai_provider import OpenAIProvider


def _events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _provider(monkeypatch, tmp_path: Path, response=None, error=None):
    monkeypatch.setenv("OPENAI_API_KEY", "API_KEY_SENTINEL")
    class Responses:
        def create(self, **_kwargs):
            if error is not None: raise error
            return response
    telemetry = HostAIAgentObservability(tmp_path)
    provider = OpenAIProvider(client_factory=lambda **_kwargs: SimpleNamespace(responses=Responses()))
    request = AgentTurnRequest(
        messages=[{"role": "user", "content": "PROMPT_SENTINEL"}], allowed_tools=[],
        request_id="HAA-OBS", conversation_context={"request_id": "HTTP-OBS"},
        telemetry=telemetry, agent_step=1,
    )
    return provider, request, telemetry.path


def test_response_shape_function_call_y_log_seguro(monkeypatch, tmp_path: Path):
    item = SimpleNamespace(type="function_call", name="consultar_estado_stock", arguments='{"consulta":"resumen","secret":"ARG_SENTINEL"}', call_id="c1")
    response = SimpleNamespace(id="resp-safe", status="completed", output=[item], output_text="", incomplete_details=None, usage=None)
    provider, request, path = _provider(monkeypatch, tmp_path, response=response)
    provider.ejecutar_turn_agente(request)
    events = _events(path); shape = next(e for e in events if e["event_type"] == "provider_response_shape")
    assert shape["request_id"] == "HTTP-OBS" and shape["agent_run_id"] == "HAA-OBS"
    assert shape["output_item_types"] == ["function_call"] and shape["function_call_count"] == 1
    serialized = path.read_text(encoding="utf-8")
    assert all(value not in serialized for value in ["API_KEY_SENTINEL", "PROMPT_SENTINEL", "ARG_SENTINEL", "TOOL_RESULT_SENTINEL"])


def test_empty_json_y_schema_errors_quedan_diferenciados(monkeypatch, tmp_path: Path):
    cases = [
        (SimpleNamespace(id="r1", status="completed", output=[], output_text="", incomplete_details=None, usage=None), "empty_output"),
        (SimpleNamespace(id="r2", status="completed", output=[], output_text="no-json", incomplete_details=None, usage=None), "json_parse_error"),
        (SimpleNamespace(id="r3", status="completed", output=[], output_text='{"answer":"x"}', incomplete_details=None, usage=None), "final_schema_invalid"),
    ]
    for index, (response, expected) in enumerate(cases):
        provider, request, path = _provider(monkeypatch, tmp_path / str(index), response=response)
        result = provider.ejecutar_turn_agente(request)
        assert result.safe_error == expected
        assert any(e.get("error_category") == expected for e in _events(path))


def test_bad_request_y_schema_error_sdk_sin_mensaje(monkeypatch, tmp_path: Path):
    for index, (error, expected) in enumerate([
        (type("BadRequestError", (Exception,), {"status_code": 400, "code": "bad_request"})("SECRET"), "api_bad_request"),
        (type("BadRequestError", (Exception,), {"status_code": 400, "code": "response_format_schema"})("SECRET"), "api_schema_error"),
    ]):
        provider, request, path = _provider(monkeypatch, tmp_path / str(index), error=error)
        assert provider.ejecutar_turn_agente(request).safe_error == expected
        assert expected in path.read_text(encoding="utf-8") and "SECRET" not in path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("exception_name", "status_code", "error_code", "error_type", "expected_category"),
    [
        ("BadRequestError", 400, "bad_request", "invalid_request_error", "api_bad_request"),
        ("AuthenticationError", 401, "invalid_api_key", "authentication_error", "provider_runtime_error"),
        ("PermissionDeniedError", 403, "permission_denied", "permission_error", "provider_runtime_error"),
        ("RateLimitError", 429, "rate_limit_exceeded", "rate_limit_error", "provider_runtime_error"),
        ("APITimeoutError", None, "", "timeout_error", "api_timeout"),
        ("APIConnectionError", None, "", "connection_error", "api_connection_error"),
        ("UnexpectedProviderFailure", None, "", "", "provider_runtime_error"),
    ],
)
def test_error_provider_conserva_solo_metadatos_seguros(
    monkeypatch, tmp_path: Path, exception_name, status_code, error_code, error_type, expected_category
):
    attrs = {
        "status_code": status_code,
        "request_id": "req_OPENAI_SAFE",
        "body": {
            "error": {
                "code": error_code,
                "type": error_type,
                "message": "BODY_SECRET_SENTINEL",
                "internal": {"prompt": "PROMPT_SECRET_SENTINEL"},
            }
        },
    }
    error = type(exception_name, (Exception,), attrs)("EXCEPTION_SECRET_SENTINEL")
    provider, request, path = _provider(monkeypatch, tmp_path, error=error)
    request.allowed_tools = [{"tool_id": "consultar_estado_stock", "description": "Stock", "input_schema": {"type": "object"}}]
    request.conversation_context["intelligence_route"] = {"model": "gpt-5-mini", "reasoning_effort": "low"}

    result = provider.ejecutar_turn_agente(request)

    assert result.safe_error == expected_category
    event = next(e for e in _events(path) if e["event_type"] == "agent_error")
    assert event["exception_type"] == exception_name
    assert event.get("status_code") == status_code
    assert event["error_code"] == error_code
    assert event["error_type"] == error_type
    assert event["openai_request_id"] == "req_OPENAI_SAFE"
    assert event["model"] == "gpt-5-mini" and event["reasoning"] == "low"
    assert event["tool_count"] == 1 and event["round"] == 1
    serialized = path.read_text(encoding="utf-8")
    assert all(secret not in serialized for secret in (
        "API_KEY_SENTINEL", "PROMPT_SENTINEL", "BODY_SECRET_SENTINEL",
        "PROMPT_SECRET_SENTINEL", "EXCEPTION_SECRET_SENTINEL",
    ))


def test_request_id_http_se_correlaciona_con_agent_run_y_fallback(monkeypatch, tmp_path: Path):
    captured = {}
    def run(self, _message, conversation_context=None):
        captured.update(conversation_context or {})
        telemetry = captured["telemetry"]
        telemetry.emit("general_agent_attempt", request_id=captured["request_id"], agent_run_id="HAA-HTTP", enabled=True, attempted=True)
        return AgentRunResult(False, request_id="HAA-HTTP", provider="FAKE", model="fake", steps=1, safe_error="grounding_failed", grounding_requirement="INTERNAL_DATA_REQUIRED")
    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    monkeypatch.setattr(HostAIAgent, "run", run)
    api = HostAIPlatformAPI(base_dir=tmp_path)
    response = api.handle(ApiRequest(method="POST", path="/api/v1/chat", request_id="HTTP-KNOWN", body={"mensaje": "consulta", "contexto": {}}))
    assert response.payload["chat"]["datos"]["general_agent"]["termination_reason"] == "grounding_failed"
    path = tmp_path / "DATOS" / "logs" / "host_ai_general_agent.jsonl"
    events = _events(path)
    assert all(e.get("request_id") == "HTTP-KNOWN" for e in events)
    assert any(e.get("agent_run_id") == "HAA-HTTP" for e in events)
    fallback = next(e for e in events if e["event_type"] == "agent_fallback")
    assert fallback["reason"] == "grounding_failed" and fallback["normalized_reason"] == "grounding_failed"
