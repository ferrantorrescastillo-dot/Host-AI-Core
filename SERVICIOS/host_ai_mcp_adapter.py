from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, is_dataclass
from typing import Any
import logging
import time
import uuid

from SERVICIOS.host_ai_agent_policy import HostAIAgentPolicy
from SERVICIOS.host_ai_authorized_execution_context import TOOL_READ_SCOPES, AuthorizedExecutionContext
from SERVICIOS.host_ai_tool_catalog import HostAIToolCatalog


LOGGER = logging.getLogger("host_ai.mcp")
UNTRUSTED_DATA_LABEL = "UNTRUSTED_DATA"


class HostAIMCPError(ValueError):
    """Error publico y saneado de una llamada MCP local."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.public_message = message


class HostAIMCPAdapter:
    """Adaptador local/dev entre MCP y las capabilities READ autorizadas."""

    def __init__(self, catalog: HostAIToolCatalog, executor: Any, policy: HostAIAgentPolicy | None = None) -> None:
        self.catalog = catalog
        self.executor = executor
        self.policy = policy or HostAIAgentPolicy()

    def list_tools(self) -> list[dict[str, Any]]:
        return [self._mcp_definition(tool) for tool in self.catalog.effective_tools()]

    def call_tool(
        self,
        tool_id: str,
        arguments: dict[str, Any] | None = None,
        *,
        request_id: str | None = None,
        execution_context: AuthorizedExecutionContext | None = None,
        require_auth: bool = False,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        call_id = str(request_id or f"MCP-{uuid.uuid4()}")
        tools = self.catalog.effective_tools()
        if require_auth:
            context_authorized, context_reason = self.policy.authorize_context(str(tool_id or ""), execution_context)
            if not context_authorized:
                self._audit(call_id, tool_id, started, authorized=False, executed=False, result_status="REJECTED", context=execution_context)
                raise HostAIMCPError("access_denied", f"MCP request rejected: {context_reason}.")
        authorized, reason = self.policy.authorize(str(tool_id or ""), arguments or {}, tools)
        if not authorized:
            self._audit(call_id, tool_id, started, authorized=False, executed=False, result_status="REJECTED", context=execution_context)
            code = "tool_not_allowed" if reason in {"tool_not_allowed", "tool_type_not_allowed"} else "invalid_arguments"
            raise HostAIMCPError(code, f"MCP request rejected: {reason}.")

        if execution_context is None:
            result = self.executor.execute_agent_read(str(tool_id), deepcopy(arguments or {}))
        else:
            result = self.executor.execute_agent_read(
                str(tool_id), deepcopy(arguments or {}), execution_context=execution_context,
            )
        result_data = result.to_dict() if hasattr(result, "to_dict") else asdict(result) if is_dataclass(result) else dict(result or {})
        public = self._sanitize(result_data)
        datos = dict(public.get("datos") or {})
        datos["solo_lectura"] = True
        datos["datos_reales_modificados"] = False
        public["datos"] = datos
        public["solo_lectura"] = True
        public["datos_reales_modificados"] = False
        public["untrusted_data"] = True
        public["data_label"] = UNTRUSTED_DATA_LABEL

        status = str(public.get("estado") or "ERROR")
        self._audit(call_id, tool_id, started, authorized=True, executed=True, result_status=status, context=execution_context)
        return {
            "structuredContent": public,
            "content": [{"type": "text", "text": f"{UNTRUSTED_DATA_LABEL}: resultado estructurado disponible."}],
            "isError": status == "ERROR",
        }

    @staticmethod
    def _mcp_definition(tool: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": str(tool["tool_id"]),
            "description": str(tool.get("description") or ""),
            "inputSchema": deepcopy(tool.get("input_schema") or {"type": "object"}),
            "outputSchema": deepcopy(tool.get("result_schema") or {"type": "object"}),
            "annotations": {
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
        }

    @classmethod
    def _sanitize(cls, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            return {str(key): cls._sanitize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._sanitize(item) for item in value[:10]]
        return str(value)

    @staticmethod
    def _audit(request_id: str, tool_id: str, started: float, *, authorized: bool, executed: bool, result_status: str, context: AuthorizedExecutionContext | None = None) -> None:
        LOGGER.info(
            "mcp_tool_audit %s",
            {
                "request_id": request_id,
                "tool_id": str(tool_id or ""),
                "user_id": str(context.user_id if context else ""),
                "tenant_id": str(context.tenant_id if context else ""),
                "required_scope": str(TOOL_READ_SCOPES.get(str(tool_id or "")) or ""),
                "duration_ms": int((time.perf_counter() - started) * 1000),
                "authorized": authorized,
                "executed": executed,
                "result_status": result_status,
            },
        )


__all__ = ["HostAIMCPAdapter", "HostAIMCPError", "UNTRUSTED_DATA_LABEL"]
