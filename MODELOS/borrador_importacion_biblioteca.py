from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class DraftStatus(str, Enum):
    PENDIENTE_REVISION = "PENDIENTE_REVISION"
    EN_REVISION = "EN_REVISION"
    CONFIRMADA = "CONFIRMADA"


class RecipeEntityType(str, Enum):
    PRINCIPAL = "PRINCIPAL"
    SUBELABORACION = "SUBELABORACION"
    COMPONENTE = "COMPONENTE"
    SECCION = "SECCION"
    DESCARTAR = "DESCARTAR"


class DraftIssueLevel(str, Enum):
    ERROR = "ERROR"
    ADVERTENCIA = "ADVERTENCIA"
    SUGERENCIA = "SUGERENCIA"


@dataclass
class DraftIssue:
    code: str
    level: DraftIssueLevel
    message: str
    field: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "level": self.level.value}


@dataclass
class IngredientDraft:
    id: str
    original_text: str
    quantity_raw: str
    quantity: float | None
    unit_raw: str
    unit: str | None
    name_raw: str
    normalized_name: str
    observations: str = ""
    article_id: str | None = None
    article_candidates: list[dict[str, Any]] = field(default_factory=list)
    relation_status: str = "SIN_RELACIONAR"
    confidence: float = 0.0
    validation_errors: list[DraftIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["validation_errors"] = [item.to_dict() for item in self.validation_errors]
        return data


@dataclass
class RecipeDraft:
    id: str
    title: str
    entity_type: RecipeEntityType
    parent_recipe_id: str | None
    order: int
    description: str
    ingredients: list[IngredientDraft]
    procedure: list[str]
    yield_value: float | None
    servings: float | None
    times: dict[str, Any]
    temperatures: list[Any]
    notes: str
    source_blocks: list[str]
    confidence: float
    proposed_action: str
    duplicate_candidates: list[dict[str, Any]]
    validation_errors: list[DraftIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["entity_type"] = self.entity_type.value
        data["ingredients"] = [item.to_dict() for item in self.ingredients]
        data["validation_errors"] = [item.to_dict() for item in self.validation_errors]
        return data


@dataclass
class ImportDraft:
    id: str
    document_id: str
    status: DraftStatus
    classification: str
    confidence: float
    recipes: list[RecipeDraft]
    warnings: list[DraftIssue]
    conflicts: list[DraftIssue]
    version: int
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "status": self.status.value,
            "classification": self.classification,
            "confidence": self.confidence,
            "recipes": [item.to_dict() for item in self.recipes],
            "warnings": [item.to_dict() for item in self.warnings],
            "conflicts": [item.to_dict() for item in self.conflicts],
            "version": self.version,
            "draft_version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "persisted": True,
            "confirmation_available": True,
        }


__all__ = [
    "DraftIssue",
    "DraftIssueLevel",
    "DraftStatus",
    "ImportDraft",
    "IngredientDraft",
    "RecipeDraft",
    "RecipeEntityType",
]
