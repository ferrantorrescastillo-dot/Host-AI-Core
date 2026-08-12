from __future__ import annotations

import json
import os
from typing import Any, Callable

from SERVICIOS.host_ai_engine.models import HostAIEngineRequest, HostAIProviderResult
from SERVICIOS.host_ai_engine.providers import HostAIProviderBase


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
        return (
            f"Pregunta del usuario: {question}\n"
            "Contexto determinista autorizado (JSON):\n"
            f"{serialized}\n"
            "Responde usando exclusivamente este contexto para datos, cantidades y unidades. "
            "No recalcules cifras, no inventes datos y no afirmes haber modificado Stock."
            f"{selection_instruction}"
            f"{read_instruction}"
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
