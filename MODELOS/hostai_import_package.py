from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


HOST_AI_IMPORT_PACKAGE_SCHEMA = "hostai.import.package"
HOST_AI_IMPORT_PACKAGE_VERSION = "0.1"


class HostAIImportPackageError(ValueError):
    """Paquete externo inválido o inseguro; nunca debe alcanzar PREVIEW/CONFIRM."""


@dataclass(frozen=True)
class HostAIImportPackage:
    schema: str
    version: str
    metadata: dict[str, Any]
    recipes: list[dict[str, Any]] = field(default_factory=list)
    articles: list[dict[str, Any]] = field(default_factory=list)
    suppliers: list[dict[str, Any]] = field(default_factory=list)
    menus: list[dict[str, Any]] = field(default_factory=list)
    relations: list[dict[str, Any]] = field(default_factory=list)
    ambiguities: list[dict[str, Any]] = field(default_factory=list)
    variant_groups: list[dict[str, Any]] = field(default_factory=list)
    warnings: tuple[str, ...] = ()


def hostai_import_package_json_schema() -> dict[str, Any]:
    """Representación exportable del contrato 0.1 validado por el adaptador."""
    entity = {"type": "object", "additionalProperties": True}
    named_entity = {
        "type": "object", "required": ["name"],
        "properties": {"name": {"type": "string", "minLength": 1}},
        "additionalProperties": True,
    }
    collections = {
        name: {"type": "array", "items": named_entity if name in {
            "recipes", "articles", "suppliers", "menus",
        } else entity, "default": []}
        for name in (
            "recipes", "articles", "suppliers", "menus", "relations",
            "ambiguities", "variant_groups",
        )
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{HOST_AI_IMPORT_PACKAGE_SCHEMA}/{HOST_AI_IMPORT_PACKAGE_VERSION}",
        "title": "HostAIImportPackage",
        "type": "object",
        "required": ["schema", "version", "metadata"],
        "properties": {
            "schema": {"const": HOST_AI_IMPORT_PACKAGE_SCHEMA},
            "version": {"const": HOST_AI_IMPORT_PACKAGE_VERSION},
            "metadata": {"type": "object"},
            **collections,
        },
        "additionalProperties": True,
        "x-hostai-security": {
            "proposal_only": True,
            "forbidden_authority": [
                "stock", "lots", "movements", "receipts", "purchases",
                "permissions", "canonical ids", "real purchase prices",
            ],
        },
    }
