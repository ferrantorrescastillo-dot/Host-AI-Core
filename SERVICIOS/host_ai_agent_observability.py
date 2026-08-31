from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any


class HostAIAgentObservability:
    """Append-only, metadata-only audit for General Agent turns."""

    ALLOWED_FIELDS = {
        "request_id", "agent_run_id", "provider", "model", "agent_step",
        "event_type", "reason", "normalized_reason", "duration_ms",
        "response_id", "response_status", "output_item_types",
        "function_call_count", "has_output_text", "output_text_length",
        "has_refusal", "has_incomplete_details", "tool_id", "authorized",
        "executed", "grounding_requirement", "retry_count", "error_category",
        "safe_error_code", "parser_result_kind", "json_parse_ok",
        "schema_validation_ok", "fallback_selected", "enabled", "attempted",
        "provider_timeout_seconds", "agent_timeout_seconds", "elapsed_ms", "remaining_ms",
        "function_call_index", "tool_call_disposition", "tool_call_argument_hash",
        "remaining_tool_budget", "same_tool_execution_count", "duplicate_of_call_id",
        "planning_phase", "selection_rank", "selected_for_execution", "rejection_reason",
        "model_tier", "reasoning_effort", "routing_reason", "workflow_type",
        "tool_result_size", "agent_round",
        "context_message_count", "context_size_chars", "context_size_json",
        "tool_result_count", "largest_tool_result_size",
        "provider_input_size", "provider_message_count", "provider_tools_count",
        "provider_duration_ms", "provider_call_started", "provider_call_finished",
        "exception_type", "status_code", "error_code", "error_type",
        "openai_request_id", "reasoning", "tool_count", "round",
        "initial_tool_budget", "research_completion_reason", "final_answer_source",
        "general_agent_candidate", "provider_connected", "supports_tool_calling", "selected_path",
    }

    def __init__(self, base_dir: Path) -> None:
        self.path = Path(base_dir).resolve() / "DATOS" / "logs" / "host_ai_general_agent.jsonl"
        self._lock = Lock()

    def emit(self, event_type: str, **metadata: Any) -> None:
        payload = {"timestamp": datetime.now().isoformat(timespec="milliseconds"), "event_type": str(event_type)}
        for key, value in metadata.items():
            if key in self.ALLOWED_FIELDS and value is not None:
                payload[key] = value
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


__all__ = ["HostAIAgentObservability"]
