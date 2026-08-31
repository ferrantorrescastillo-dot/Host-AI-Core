from __future__ import annotations

from copy import deepcopy
from typing import Any

from MODELOS.hostai_import_package import (
    HOST_AI_IMPORT_PACKAGE_SCHEMA,
    HOST_AI_IMPORT_PACKAGE_VERSION,
    HostAIImportPackageError,
)


PROTOTYPE_SCHEMA = "hostai.chatgpt_import.v0.1"


class ChatGPTImportV01Converter:
    """Migración explícita del prototipo ChatGPT al contrato canónico 0.1."""

    TOP_LEVEL_FIELDS = {
        "schema_version", "generator", "source_document", "interpretation_contract",
        "extraction_summary", "catalog_items", "ignored_source_rows",
        "recipes_and_elaborations", "variant_groups", "menus_and_containers",
        "supplemental_complex_context", "hostai_expected_next_stage", "semantic_findings",
    }

    def convert(self, prototype: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(prototype, dict):
            raise HostAIImportPackageError("El prototipo ChatGPT debe ser un objeto JSON.")
        if prototype.get("schema_version") != PROTOTYPE_SCHEMA:
            raise HostAIImportPackageError(
                f"Se esperaba {PROTOTYPE_SCHEMA}; no se intentará una migración implícita."
            )
        recipes = [deepcopy(item) for item in prototype.get("recipes_and_elaborations") or []]
        articles = [self._article(item) for item in prototype.get("catalog_items") or []]
        suppliers = self._suppliers(prototype.get("catalog_items") or [])
        menus = [self._menu(item) for item in prototype.get("menus_and_containers") or []]
        menus.extend(self._context(item) for item in prototype.get("supplemental_complex_context") or [])
        ambiguities = [self._finding(item) for item in prototype.get("semantic_findings") or []]

        grouped_ids = {
            str(item.get("variant_group_id")) for item in recipes if item.get("variant_group_id")
        }
        normal_recipes = [self._recipe(item) for item in recipes if not item.get("variant_group_id")]
        variant_groups: list[dict[str, Any]] = []
        for group_id in sorted(grouped_ids):
            versions = [item for item in recipes if str(item.get("variant_group_id")) == group_id]
            if self._same_structure(versions):
                merged = self._recipe(versions[0])
                merged["occurrences"] = [
                    self._occurrence(occurrence)
                    for version in versions for occurrence in version.get("occurrences") or []
                ]
                yields = [{
                    "value": item.get("rendimiento"),
                    "unit": item.get("unidad_rendimiento_origen"),
                    "occurrences": deepcopy(item.get("occurrences") or []),
                } for item in versions]
                if len({(str(item["value"]), str(item["unit"])) for item in yields}) > 1:
                    merged["yield"] = None
                    merged["yield_unit"] = None
                    merged.setdefault("observed", {})["yield_versions"] = yields
                    ambiguities.append({
                        "type": "POSSIBLE_SCALED_OCCURRENCE", "name": merged["name"],
                        "reason": "Misma estructura de ingredientes con rendimientos de origen distintos.",
                        "options": yields, "provenance": {"prototype_variant_group_id": group_id},
                    })
                normal_recipes.append(merged)
            else:
                variant_groups.append({
                    "name": versions[0].get("nombre") or group_id,
                    "versions": [self._recipe(item) for item in versions],
                    "provenance": {"prototype_variant_group_id": group_id},
                })

        unknown = sorted(set(prototype) - self.TOP_LEVEL_FIELDS)
        migration_warnings = [
            {"type": "CAMPO_NO_MIGRADO", "path": f"$.{field}", "reason": "Campo superior desconocido."}
            for field in unknown
        ]
        return {
            "schema": HOST_AI_IMPORT_PACKAGE_SCHEMA,
            "version": HOST_AI_IMPORT_PACKAGE_VERSION,
            "metadata": {
                "source": deepcopy(prototype.get("source_document") or {}),
                "extractor": deepcopy(prototype.get("generator") or {}),
                "prototype_schema": PROTOTYPE_SCHEMA,
                "interpretation_contract": deepcopy(prototype.get("interpretation_contract") or {}),
                "extraction_summary": deepcopy(prototype.get("extraction_summary") or {}),
                "ignored_source_rows": deepcopy(prototype.get("ignored_source_rows") or []),
                "expected_next_stage": deepcopy(prototype.get("hostai_expected_next_stage") or {}),
                "migration_warnings": migration_warnings,
            },
            "recipes": normal_recipes,
            "articles": articles,
            "suppliers": suppliers,
            "menus": menus,
            "relations": [],
            "ambiguities": ambiguities,
            "variant_groups": variant_groups,
        }

    @staticmethod
    def _occurrence(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "sheet": item.get("sheet"), "row": item.get("recipe_row") or item.get("row"),
            "ingredient_header_row": item.get("ingredient_header_row"),
            "context": deepcopy(item.get("context") or []),
        }

    def _recipe(self, item: dict[str, Any]) -> dict[str, Any]:
        ingredients = []
        for ingredient in item.get("ingredientes") or []:
            ingredients.append({
                "name": ingredient.get("nombre"), "quantity": ingredient.get("cantidad_origen"),
                "quantity_text": str(ingredient.get("cantidad_origen") or ""),
                "unit": ingredient.get("unidad_columna_origen"),
                "observed": deepcopy(ingredient),
                "provenance": {"row": ingredient.get("source_row")},
            })
        return {
            "source_id": None, "name": item.get("nombre"),
            "aliases": [item.get("nombre_normalizado_chatgpt")] if item.get("nombre_normalizado_chatgpt") else [],
            "entity_type": "ELABORACION_INTERNA",
            "ingredients": ingredients, "yield": item.get("rendimiento"),
            "yield_unit": item.get("unidad_rendimiento_origen"),
            "document_costs": [{
                "type": "PRECIO_DOCUMENTO", "total": item.get("coste_total_origen"),
                "unit_cost": item.get("coste_unitario_origen"),
                "unit_label": item.get("coste_unitario_label_origen"),
            }],
            "occurrences": [self._occurrence(value) for value in item.get("occurrences") or []],
            "confidence": item.get("confidence_extraction"),
            "observed": deepcopy(item),
            "interpretation": {"prototype_entity_type": item.get("entity_type_chatgpt")},
        }

    @staticmethod
    def _article(item: dict[str, Any]) -> dict[str, Any]:
        price = item.get("precio_origen")
        document_price = None if price is None or price == "" else {
            "value": price, "type": "PRECIO_REFERENCIA_IMPORTADO",
            "context": deepcopy(item.get("precio_semantica")),
        }
        return {
            "source_code": item.get("codigo_origen"), "name": item.get("nombre"),
            "family": item.get("familia_origen"), "supplier": item.get("proveedor_origen"),
            "document_price": document_price,
            "confidence": item.get("confidence_classification"),
            "observed": deepcopy(item),
            "interpretation": {
                "classification": item.get("clasificacion_chatgpt"),
                "reason": item.get("classification_reason"),
                "supplier_semantics": deepcopy(item.get("proveedor_semantica")),
            },
            "provenance": {"row": item.get("source_row")},
        }

    @staticmethod
    def _suppliers(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        names: dict[str, str] = {}
        for item in items:
            name = str(item.get("proveedor_origen") or "").strip()
            if name:
                names.setdefault(name.casefold(), name)
        return [{"name": value, "provenance": {"source": "catalog_items.proveedor_origen"}}
                for value in names.values()]

    @staticmethod
    def _menu(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": item.get("nombre"), "kind": "MENU",
            "items": deepcopy(item.get("items") or []),
            "observed": deepcopy(item), "confidence": item.get("confidence_extraction"),
            "provenance": deepcopy(item.get("source") or {}),
        }

    @staticmethod
    def _context(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": item.get("sheet") or "Contexto documental", "kind": "CONTEXT",
            "items": deepcopy(item.get("rows") or []), "observed": deepcopy(item),
            "interpretation": {"classification": item.get("classification")},
            "provenance": {"sheet": item.get("sheet")},
        }

    @staticmethod
    def _finding(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": item.get("type") or "REQUIERE_REVISION",
            "name": item.get("source_token") or item.get("pattern") or item.get("name") or "Hallazgo semántico",
            "reason": item.get("finding") or "Requiere revisión.",
            "confidence": item.get("confidence"), "observed": deepcopy(item),
        }

    @staticmethod
    def _same_structure(versions: list[dict[str, Any]]) -> bool:
        def signature(item: dict[str, Any]) -> tuple[tuple[str, str, str], ...]:
            return tuple(sorted((
                str(ingredient.get("nombre") or "").strip().casefold(),
                str(ingredient.get("cantidad_origen") or ""),
                str(ingredient.get("unidad_columna_origen") or "").strip().casefold(),
            ) for ingredient in item.get("ingredientes") or []))
        return bool(versions) and len({signature(item) for item in versions}) == 1
