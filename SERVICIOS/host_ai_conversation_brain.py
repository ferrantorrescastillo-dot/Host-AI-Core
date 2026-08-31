from __future__ import annotations

from dataclasses import dataclass, field
import os
import re
import unicodedata
from typing import Any


def _normalized(text: Any) -> str:
    value = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii")
    return " ".join(value.lower().split())


@dataclass(frozen=True)
class AIModelConfiguration:
    """Configuracion de modelos sin acoplar los workflows a un proveedor."""

    fast: str
    standard: str
    frontier: str
    reasoning_low: str = "low"
    reasoning_medium: str = "medium"
    reasoning_high: str = "high"

    @classmethod
    def from_environment(cls) -> "AIModelConfiguration":
        default = str(os.getenv("OPENAI_MODEL") or "gpt-5-mini").strip()
        return cls(
            fast=str(os.getenv("AI_MODEL_FAST") or default).strip(),
            standard=str(os.getenv("AI_MODEL_STANDARD") or default).strip(),
            frontier=str(os.getenv("AI_MODEL_FRONTIER") or default).strip(),
            reasoning_low=cls._reasoning_from_environment("AI_REASONING_LOW", "low"),
            reasoning_medium=cls._reasoning_from_environment("AI_REASONING_MEDIUM", "medium"),
            reasoning_high=cls._reasoning_from_environment("AI_REASONING_HIGH", "high"),
        )

    def model_for(self, tier: str) -> str:
        return getattr(self, str(tier or "standard").lower(), self.standard)

    def effort_for(self, level: str) -> str:
        return getattr(self, f"reasoning_{str(level or 'medium').lower()}", self.reasoning_medium)

    @staticmethod
    def _reasoning_from_environment(name: str, default: str) -> str:
        value = str(os.getenv(name) or default).strip().lower()
        return value if value in {"low", "medium", "high"} else default


@dataclass(frozen=True)
class ConversationRoute:
    tier: str
    model: str
    reasoning_effort: str
    reason: str
    workflow_type: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "tier": self.tier,
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "reason": self.reason,
            "workflow_type": self.workflow_type,
        }


@dataclass
class WorkflowState:
    objective: str = ""
    workflow_type: str = ""
    active_entity: dict[str, Any] = field(default_factory=dict)
    checked: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)
    user_decisions: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "workflow_type": self.workflow_type,
            "active_entity": dict(self.active_entity),
            "checked": list(self.checked),
            "pending": list(self.pending),
            "user_decisions": dict(self.user_decisions),
        }


class HostAIConversationBrain:
    """Decide el nivel de inteligencia y conserva el objetivo conversacional.

    No consulta ni modifica datos: los motores y tools siguen siendo la fuente de
    verdad. Este componente solo prepara una ruta explícita para el agente.
    """

    _ESCALATION_PATTERNS = (
        "piensalo mejor", "no me convence", "analizalo bien", "analizalo a fondo",
        "dame una respuesta mejor", "hazlo mas profesional", "usa la ia buena",
        "mejor plan posible", "revisalo otra vez", "profundiza",
    )
    _RECIPE_PATTERNS = (
        "terminala", "terminamela", "completar esta receta", "completa esta receta",
        "que le falta", "dejame esta receta lista", "proponer una receta con ia",
        "propon una receta con ia", "proponme una receta",
    )
    _PRODUCTION_PATTERNS = (
        "hazme la produccion", "preparame la produccion", "plan de produccion", "organiza la produccion",
        "produccion de la boda", "produccion del evento",
    )
    _COMPLEX_TERMS = {
        "planifica", "planificacion", "dependencia", "prioriza", "prioridad",
        "anomalia", "contradictorio", "investiga", "diagnostica", "comparar",
        "evento", "produccion", "escandallo", "rendimiento", "subelaboracion",
    }

    def __init__(self, config: AIModelConfiguration | None = None) -> None:
        self.config = config or AIModelConfiguration.from_environment()

    def prepare_turn(
        self,
        message: str,
        state: dict[str, Any] | None = None,
        active_entity: dict[str, Any] | None = None,
    ) -> tuple[ConversationRoute, WorkflowState]:
        text = _normalized(message)
        workflow_type = self._workflow_type(text, state)
        route = self._route(text, workflow_type)
        workflow = self._workflow_state(text, state, active_entity, workflow_type)
        return route, workflow

    def record_tool_results(
        self,
        state: dict[str, Any] | None,
        executed_tools: list[str] | None,
    ) -> WorkflowState:
        previous = dict(state or {})
        checked = [str(item) for item in list(previous.get("checked") or []) if str(item)]
        for tool_id in list(executed_tools or []):
            if tool_id and tool_id not in checked:
                checked.append(str(tool_id))
        return WorkflowState(
            objective=str(previous.get("objective") or ""),
            workflow_type=str(previous.get("workflow_type") or ""),
            active_entity=dict(previous.get("active_entity") or {}),
            checked=checked[-20:],
            pending=[str(item) for item in list(previous.get("pending") or []) if str(item)],
            user_decisions=dict(previous.get("user_decisions") or {}),
        )

    def _route(self, text: str, workflow_type: str) -> ConversationRoute:
        if any(pattern in text for pattern in self._ESCALATION_PATTERNS):
            return self._make_route("frontier", "high", "user_requested_deeper_review", workflow_type)
        if workflow_type in {"recipe_completion", "production_planning"}:
            return self._make_route("frontier", "high", workflow_type, workflow_type)
        complexity = sum(term in text for term in self._COMPLEX_TERMS)
        if complexity >= 2:
            return self._make_route("frontier", "high", "multi_factor_operational_analysis", workflow_type)
        if complexity == 1 or len(re.findall(r"\b\w+\b", text)) > 20:
            return self._make_route("standard", "medium", "contextual_analysis", workflow_type)
        return self._make_route("fast", "low", "direct_conversation_or_read", workflow_type)

    def _make_route(self, tier: str, effort: str, reason: str, workflow_type: str) -> ConversationRoute:
        return ConversationRoute(tier, self.config.model_for(tier), self.config.effort_for(effort), reason, workflow_type)

    def _workflow_type(self, text: str, state: dict[str, Any] | None) -> str:
        if any(pattern in text for pattern in self._RECIPE_PATTERNS):
            return "recipe_completion"
        if any(pattern in text for pattern in self._PRODUCTION_PATTERNS):
            return "production_planning"
        if sum(term in text for term in self._COMPLEX_TERMS) >= 2:
            return "operational_research"
        previous = str((state or {}).get("workflow_type") or "")
        return previous if previous and text else ""

    def _workflow_state(
        self,
        text: str,
        state: dict[str, Any] | None,
        active_entity: dict[str, Any] | None,
        workflow_type: str,
    ) -> WorkflowState:
        previous = dict(state or {})
        is_new = bool(workflow_type) and workflow_type != str(previous.get("workflow_type") or "")
        if is_new:
            objective = {
                "recipe_completion": "Completar la receta activa con datos verificados y propuestas separadas.",
                "production_planning": "Preparar un plan de producción basado en los datos operativos disponibles.",
                "operational_research": "Resolver el objetivo operativo original investigando todas las fuentes READ necesarias.",
            }.get(workflow_type, "")
            pending = {
                "recipe_completion": ["receta", "ingredientes", "escandallo", "procedimiento"],
                "production_planning": ["evento", "menu", "cantidades", "dependencias", "bloqueos"],
                "operational_research": ["entidades", "relaciones", "stock", "compras", "incidencias"],
            }.get(workflow_type, [])
            return WorkflowState(objective, workflow_type, dict(active_entity or {}), [], pending)
        return WorkflowState(
            objective=str(previous.get("objective") or ""),
            workflow_type=workflow_type,
            active_entity=dict(active_entity or previous.get("active_entity") or {}),
            checked=[str(item) for item in list(previous.get("checked") or []) if str(item)],
            pending=[str(item) for item in list(previous.get("pending") or []) if str(item)],
            user_decisions=dict(previous.get("user_decisions") or {}),
        )


__all__ = ["AIModelConfiguration", "ConversationRoute", "HostAIConversationBrain", "WorkflowState"]
