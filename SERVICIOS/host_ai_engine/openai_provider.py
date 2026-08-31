from __future__ import annotations

import json
import os
import time
from typing import Any, Callable

from SERVICIOS.host_ai_engine.models import HostAIEngineRequest, HostAIProviderResult
from SERVICIOS.host_ai_engine.providers import HostAIProviderBase
from SERVICIOS.host_ai_agent_models import (
    AgentTurnRequest, AgentTurnResult, FINAL_RESPONSE, TOOL_CALL, ToolCall,
    GROUNDING_INTERNAL_DATA_REQUIRED, GROUNDING_NONE,
)


DEFAULT_OPENAI_MODEL = "gpt-5-mini"
DEFAULT_OPENAI_TIMEOUT_SECONDS = 30.0


class OpenAIProvider(HostAIProviderBase):
    provider_name = "OPENAI"

    def __init__(
        self,
        *,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.model_name = str(os.getenv("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL).strip()
        self._api_key = str(os.getenv("OPENAI_API_KEY") or "").strip()
        self._client_factory = client_factory
        self._client: Any | None = None

    @property
    def connected(self) -> bool:
        return bool(self._api_key and (self._client_factory or self._sdk_available()))

    @property
    def supports_tool_calling(self) -> bool:
        return True

    def ejecutar_turn_agente(self, request: AgentTurnRequest) -> AgentTurnResult:
        telemetry = request.telemetry
        effective_timeout = float(request.provider_timeout_seconds or DEFAULT_OPENAI_TIMEOUT_SECONDS)
        route = request.conversation_context.get("intelligence_route") if isinstance(request.conversation_context.get("intelligence_route"), dict) else {}
        model = str(route.get("model") or self.model_name).strip() or self.model_name
        reasoning_effort = str(route.get("reasoning_effort") or "").lower()
        common = {"request_id": str(request.conversation_context.get("request_id") or ""), "agent_run_id": request.request_id, "provider": self.provider_name, "model": model, "agent_step": request.agent_step, "round": request.agent_step, "provider_timeout_seconds": effective_timeout, "agent_timeout_seconds": request.agent_timeout_seconds, "elapsed_ms": request.elapsed_ms, "remaining_ms": request.remaining_ms, "model_tier": str(route.get("tier") or ""), "reasoning": reasoning_effort, "reasoning_effort": reasoning_effort, "routing_reason": str(route.get("reason") or ""), "workflow_type": str(route.get("workflow_type") or "")}
        if not self._api_key:
            self._emit(telemetry, "agent_error", **common, error_category="provider_runtime_error", safe_error_code="provider_not_configured")
            return AgentTurnResult(kind="", safe_error="OpenAI no esta configurado.", provider_metadata=self._agent_meta())
        try:
            request_input = self._agent_input(request.messages)
            request_tools = [{"type": "function", "name": item["tool_id"], "description": item["description"], "parameters": item["input_schema"], "strict": False} for item in request.allowed_tools]
            common["tool_count"] = len(request_tools)
            started = time.perf_counter()
            self._emit(telemetry, "provider_request", **common, provider_call_started=True, provider_message_count=len(request.messages), provider_input_size=len(json.dumps(request_input, ensure_ascii=False, default=str)), provider_tools_count=len(request_tools))
            request_kwargs = {
                "model": model,
                "instructions": str(request.system_instructions or ""),
                "input": request_input,
                "text": {"format": {"type": "json_schema", "name": "host_ai_agent_final", "strict": True, "schema": dict(request.response_schema or {})}},
                "timeout": effective_timeout,
            }
            if request_tools:
                request_kwargs["tools"] = request_tools
                request_kwargs["tool_choice"] = (
                    "required" if str(request.tool_choice_mode or "auto").lower() == "required" else "auto"
                )
            if reasoning_effort in {"low", "medium", "high"}:
                request_kwargs["reasoning"] = {"effort": reasoning_effort}
            response = self._get_client().responses.create(
                **request_kwargs,
            )
            provider_duration_ms = round((time.perf_counter() - started) * 1000, 2)
            self._emit(telemetry, "provider_complete", **common, provider_call_finished=True, provider_duration_ms=provider_duration_ms)
            output = list(getattr(response, "output", None) or [])
            item_types = [str(getattr(item, "type", "") or "unknown") for item in output]
            raw_text = str(getattr(response, "output_text", "") or "")
            self._emit(
                telemetry, "provider_response_shape", **common,
                response_id=str(getattr(response, "id", "") or ""),
                response_status=str(getattr(response, "status", "") or ""),
                output_item_types=item_types,
                function_call_count=sum(1 for value in item_types if value == "function_call"),
                has_output_text=bool(raw_text), output_text_length=len(raw_text),
                has_refusal=any(value == "refusal" for value in item_types),
                has_incomplete_details=getattr(response, "incomplete_details", None) is not None,
            )
            calls = []
            for item in output:
                if str(getattr(item, "type", "")) != "function_call":
                    continue
                raw_args = getattr(item, "arguments", {})
                try:
                    arguments = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args or {})
                except (TypeError, ValueError):
                    self._emit(telemetry, "agent_error", **common, error_category="function_call_parse_error", safe_error_code="function_call_parse_error")
                    return AgentTurnResult(kind="", safe_error="function_call_parse_error", provider_metadata=self._agent_meta(model))
                calls.append(ToolCall(str(getattr(item, "name", "")), arguments, str(getattr(item, "call_id", ""))))
            usage = self._agent_usage(getattr(response, "usage", None))
            response_meta = {**self._agent_meta(model), "response_id": str(getattr(response, "id", "") or ""), "service_tier": str(getattr(response, "service_tier", "") or "")}
            if calls:
                self._emit(telemetry, "provider_parser_result", **common, parser_result_kind=TOOL_CALL)
                return AgentTurnResult(TOOL_CALL, tool_calls=calls, usage=usage, provider_metadata=response_meta)
            raw_text = raw_text.strip()
            if not raw_text:
                self._emit(telemetry, "agent_error", **common, error_category="empty_output", safe_error_code="empty_output", json_parse_ok=False, schema_validation_ok=False)
                return AgentTurnResult(kind="", safe_error="empty_output", usage=usage, provider_metadata=response_meta)
            try:
                final = json.loads(raw_text)
            except (TypeError, ValueError):
                self._emit(telemetry, "agent_error", **common, error_category="json_parse_error", safe_error_code="json_parse_error", json_parse_ok=False, schema_validation_ok=False)
                return AgentTurnResult(kind="", safe_error="json_parse_error", usage=usage, provider_metadata=response_meta)
            requirement = str((final or {}).get("grounding_requirement") or "").upper()
            text = str((final or {}).get("answer") or "").strip()
            if requirement not in {GROUNDING_NONE, GROUNDING_INTERNAL_DATA_REQUIRED} or not text:
                self._emit(telemetry, "agent_error", **common, error_category="final_schema_invalid", safe_error_code="final_schema_invalid", json_parse_ok=True, schema_validation_ok=False)
                return AgentTurnResult(kind="", safe_error="final_schema_invalid", usage=usage, provider_metadata=response_meta)
            self._emit(telemetry, "provider_parser_result", **common, parser_result_kind=FINAL_RESPONSE, grounding_requirement=requirement, json_parse_ok=True, schema_validation_ok=True)
            return AgentTurnResult(FINAL_RESPONSE, text=text, usage=usage, provider_metadata=response_meta, grounding_requirement=requirement)
        except Exception as exc:
            category = self._agent_error_category(exc)
            error_metadata = self._agent_error_metadata(exc)
            self._emit(telemetry, "agent_error", **common, **error_metadata, error_category=category, safe_error_code=category, provider_call_finished=True, provider_duration_ms=round((time.perf_counter() - locals().get("started", time.perf_counter())) * 1000, 2))
            return AgentTurnResult(kind="", safe_error=category, provider_metadata=self._agent_meta(model))

    @staticmethod
    def _agent_input(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        output = []
        for item in messages:
            if item.get("type") == "tool_call":
                output.append({"type": "function_call", "name": item.get("tool_id"), "arguments": json.dumps(item.get("arguments") or {}, ensure_ascii=False), "call_id": item.get("call_id")})
            elif item.get("type") == "TOOL_DATA":
                output.append({"type": "function_call_output", "call_id": item.get("call_id"), "output": json.dumps({"label": "UNTRUSTED_DATA", "data": item.get("content")}, ensure_ascii=False)})
            else:
                output.append({"role": item.get("role", "user"), "content": str(item.get("content") or "")})
        return output

    def _agent_meta(self, model: str | None = None) -> dict[str, str]:
        return {"provider": self.provider_name, "model": str(model or self.model_name)}

    @staticmethod
    def _emit(telemetry: Any, event_type: str, **metadata: Any) -> None:
        if telemetry is not None:
            telemetry.emit(event_type, **metadata)

    @staticmethod
    def _agent_error_category(exc: Exception) -> str:
        name = type(exc).__name__.lower()
        status = getattr(exc, "status_code", None)
        body = getattr(exc, "body", None)
        code = str(getattr(exc, "code", "") or "").lower()
        if isinstance(body, dict):
            error = body.get("error") if isinstance(body.get("error"), dict) else body
            code = str(error.get("code") or code).lower()
        if status == 400:
            return "api_schema_error" if "schema" in code or "response_format" in code else "api_bad_request"
        if "timeout" in name:
            return "api_timeout"
        if "connection" in name:
            return "api_connection_error"
        return "provider_runtime_error"

    @staticmethod
    def _agent_error_metadata(exc: Exception) -> dict[str, Any]:
        body = getattr(exc, "body", None)
        error = body.get("error") if isinstance(body, dict) and isinstance(body.get("error"), dict) else body
        error = error if isinstance(error, dict) else {}
        status = getattr(exc, "status_code", None)
        request_id = getattr(exc, "request_id", None)
        if not request_id:
            response = getattr(exc, "response", None)
            headers = getattr(response, "headers", None)
            if headers is not None:
                request_id = headers.get("x-request-id") or headers.get("request-id")
        return {
            "exception_type": type(exc).__name__,
            "status_code": status if isinstance(status, int) else None,
            "error_code": str(error.get("code") or getattr(exc, "code", "") or ""),
            "error_type": str(error.get("type") or getattr(exc, "type", "") or ""),
            "openai_request_id": str(request_id or ""),
        }

    @staticmethod
    def _agent_usage(usage: Any) -> dict[str, Any]:
        if usage is None:
            return {}
        details_in = getattr(usage, "input_tokens_details", None)
        details_out = getattr(usage, "output_tokens_details", None)
        def detail(value: Any, key: str) -> int:
            if isinstance(value, dict): return int(value.get(key) or 0)
            return int(getattr(value, key, 0) or 0)
        return {
            "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
            "cached_input_tokens": detail(details_in, "cached_tokens"),
            "cache_write_tokens": detail(details_in, "cache_write_tokens"),
            "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
            "reasoning_tokens": detail(details_out, "reasoning_tokens"),
            "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
        }

    def ejecutar(self, request: HostAIEngineRequest) -> HostAIProviderResult:
        if not self._api_key:
            return self._error("OpenAI no está configurado: falta OPENAI_API_KEY.")
        try:
            client = self._get_client()
            response = client.responses.create(
                model=self.model_name,
                instructions=(
                    "Eres Host AI, un segundo de cocina digital. Responde en español, "
                    "de forma clara y práctica. No inventes datos operativos ni afirmes "
                    "haber ejecutado acciones. Las herramientas y motores de HOST AI "
                    "conservan la autoridad sobre stock, compras, producción y costes."
                ),
                input=self._input_text(request),
            )
            text = str(getattr(response, "output_text", "") or "").strip()
            if not text:
                return self._error("OpenAI devolvió una respuesta sin texto utilizable.")
            return HostAIProviderResult(
                ok=True,
                proveedor=self.provider_name,
                modelo=self.model_name,
                salida={"mensaje": text},
                errores=[],
                usage=self._agent_usage(getattr(response, "usage", None)),
                response_id=str(getattr(response, "id", "") or ""),
                service_tier=str(getattr(response, "service_tier", "") or ""),
            )
        except Exception as exc:  # El SDK expone subclases distintas según la versión.
            return self._error(self._safe_error_message(exc))

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        factory = self._client_factory
        if factory is None:
            from openai import OpenAI

            factory = OpenAI
        self._client = factory(
            api_key=self._api_key,
            timeout=DEFAULT_OPENAI_TIMEOUT_SECONDS,
            max_retries=0,
        )
        return self._client

    @staticmethod
    def _sdk_available() -> bool:
        try:
            import openai  # noqa: F401
        except ImportError:
            return False
        return True

    @staticmethod
    def _input_text(request: HostAIEngineRequest) -> str:
        data = dict(request.datos_enviados or {})
        question = str(data.get("pregunta") or data.get("mensaje") or "").strip()
        question = question or str(data.get("texto") or "").strip()
        tool_context = data.get("tool_context")
        if not isinstance(tool_context, dict):
            return question
        serialized = json.dumps(tool_context, ensure_ascii=False, sort_keys=True)
        selection_instruction = ""
        if tool_context.get("seleccion_resuelta") is True:
            selection_instruction = (
                " La selección conversacional ya fue resuelta de forma determinista. "
                "No vuelvas a interpretar el ordinal o identificador original; presenta únicamente articulo_seleccionado."
            )
        read_instruction = ""
        if tool_context.get("solo_lectura") is True:
            read_instruction = (
                " Esta herramienta es exclusivamente de lectura. Responde a la consulta y, como máximo, "
                "ofrece otra consulta de lectura relacionada. No sugieras escrituras, exportaciones ni capacidades "
                "que no estén explícitamente disponibles en el contexto."
            )
        production_instruction = ""
        if tool_context.get("fuente") == "produccion_real_canonica":
            production_instruction = (
                " Conserva exactamente estados, cantidades, unidades, fechas y porcentajes de Produccion. "
                "No conviertas valores null en cero, no recalcules en_curso y no sugieras haber iniciado, "
                "pausado, finalizado o modificado ninguna tarea."
            )
        return (
            f"Pregunta del usuario: {question}\n"
            "Contexto determinista autorizado (JSON):\n"
            f"{serialized}\n"
            "Responde usando exclusivamente este contexto para datos, cantidades y unidades. "
            "No recalcules cifras, no inventes datos y no afirmes haber modificado Stock."
            f"{selection_instruction}"
            f"{read_instruction}"
            f"{production_instruction}"
        )

    def _error(self, message: str) -> HostAIProviderResult:
        return HostAIProviderResult(
            ok=False,
            proveedor=self.provider_name,
            modelo=self.model_name,
            salida={},
            errores=[message],
        )

    @staticmethod
    def _safe_error_message(exc: Exception) -> str:
        name = type(exc).__name__.lower()
        status = getattr(exc, "status_code", None)
        code = str(getattr(exc, "code", "") or "").lower()
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            error = body.get("error") if isinstance(body.get("error"), dict) else body
            code = str(error.get("code") or code).lower()

        if status in {401, 403} or "auth" in name or "permission" in name:
            return "OpenAI rechazó la credencial o sus permisos."
        if code in {"insufficient_quota", "billing_hard_limit_reached"}:
            return "OpenAI no tiene cuota o crédito disponible para esta solicitud."
        if status == 429 or "ratelimit" in name or "rate_limit" in name:
            return "OpenAI ha limitado temporalmente las solicitudes. Inténtalo de nuevo más tarde."
        if "timeout" in name:
            return "OpenAI no respondió dentro del tiempo permitido."
        if "connection" in name or "network" in name:
            return "No se pudo conectar con OpenAI. Revisa la red e inténtalo de nuevo."
        return "OpenAI no pudo procesar la solicitud en este momento."


__all__ = ["OpenAIProvider", "DEFAULT_OPENAI_MODEL"]
