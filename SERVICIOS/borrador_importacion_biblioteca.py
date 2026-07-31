from __future__ import annotations

import re
import unicodedata
from copy import deepcopy
from datetime import datetime, timezone
from difflib import SequenceMatcher
from fractions import Fraction
from pathlib import Path
from typing import Any

from MODELOS.borrador_importacion_biblioteca import (
    DraftIssue,
    DraftIssueLevel,
    DraftStatus,
    ImportDraft,
    IngredientDraft,
    RecipeDraft,
    RecipeEntityType,
)
from SERVICIOS.importador_inteligente_recetas_m131 import clasificar_prefijo_articulo
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601
from SERVICIOS.schema_escandallos_555a import UNIDADES_ADMITIDAS, normalizar_unidad
from SERVICIOS.utilidades_importador_i135 import coincidencias_exactas


FRACTIONS = {"¼": 0.25, "½": 0.5, "¾": 0.75}
APPROXIMATE_QUANTITIES = {"c/s", "al gusto", "una pizca", "pizca"}
VALID_ACTIONS = {
    "CREAR_ELABORACION", "CREAR_RECETA", "ACTUALIZAR_ELABORACION",
    "ACTUALIZAR_RECETA", "CREAR_SUBELABORACION", "MANTENER_COMPONENTE", "IGNORAR",
}
VALID_RELATIONS = {
    "RELACIONADO", "COINCIDENCIA_EXACTA_PROPUESTA", "REVISAR_COINCIDENCIA",
    "SIN_RELACIONAR", "CREAR_ARTICULO_PROPUESTO", "IGNORADO",
}


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


class CulinaryQuantityParser:
    """Normaliza solo cantidades inequívocas y conserva siempre el original."""

    def parse(self, raw: Any) -> tuple[float | None, list[DraftIssue]]:
        text = str(raw or "").strip().lower()
        if not text:
            return None, []
        if text in APPROXIMATE_QUANTITIES:
            return None, [DraftIssue(
                "CANTIDAD_APROXIMADA", DraftIssueLevel.ADVERTENCIA,
                f"La cantidad «{raw}» debe revisarse antes de confirmar.", "quantity",
            )]
        if text in FRACTIONS:
            return FRACTIONS[text], []
        if re.fullmatch(r"\d+\s+\d+", text):
            return None, [DraftIssue(
                "CANTIDAD_AMBIGUA", DraftIssueLevel.ADVERTENCIA,
                f"«{raw}» puede representar una fracción, un decimal o un rango.", "quantity",
            )]
        if re.fullmatch(r"\d+(?:[.,]\d+)?-\d+(?:[.,]\d+)?", text):
            return None, [DraftIssue(
                "CANTIDAD_RANGO", DraftIssueLevel.ADVERTENCIA,
                f"El rango «{raw}» necesita una cantidad final elegida por el usuario.", "quantity",
            )]
        try:
            if re.fullmatch(r"\d+/\d+", text):
                return float(Fraction(text)), []
            return float(text.replace(",", ".")), []
        except (ValueError, ZeroDivisionError):
            return None, [DraftIssue(
                "CANTIDAD_INVALIDA", DraftIssueLevel.ERROR,
                f"No se reconoce la cantidad «{raw}».", "quantity",
            )]


class IngredientTextNormalizer:
    PARENTHESIS = re.compile(r"\s*\((?P<observation>[^()]*)\)\s*$")
    TRAILING_CONTEXT = re.compile(
        r"^(?P<name>.+?)\s+(?P<observation>para\s+.+|previamente\s+.+)$",
        re.IGNORECASE,
    )

    def split(self, raw_name: Any) -> tuple[str, str]:
        original = str(raw_name or "").strip()
        observation = ""
        match = self.PARENTHESIS.search(original)
        if match:
            observation = match.group("observation").strip()
            original = original[:match.start()].strip()
        else:
            match = self.TRAILING_CONTEXT.match(original)
            if match:
                original = match.group("name").strip()
                observation = match.group("observation").strip()
        normalized = re.sub(r"\bhueso\s+jam[oó]n\b", "hueso de jamón", original, flags=re.I)
        return normalized.strip(), observation


class IngredientAliasResolver:
    """Deriva equivalencias del catálogo; no guarda ni inventa alias."""

    ALIAS_FIELDS = ("alias", "aliases", "variantes", "variantes_detectadas", "nombre_proveedor")

    def aliases(self, article: dict[str, Any]) -> set[str]:
        values = {normalize_text(article.get("nombre"))}
        meta = dict(article.get("catalogo_maestro") or {})
        for field in self.ALIAS_FIELDS:
            raw = article.get(field, meta.get(field))
            if isinstance(raw, list):
                values.update(normalize_text(item) for item in raw)
            elif raw:
                values.add(normalize_text(raw))
        return {value for value in values if value}


class ArticleCandidateFinder:
    def __init__(self, base_dir: Path) -> None:
        self.catalog = RepositorioProductosMaestro601(base_dir)
        self.aliases = IngredientAliasResolver()

    def find(self, name: str, unit: str | None) -> dict[str, Any]:
        articles = [
            item for item in self.catalog.listar_productos(incluir_archivados=False)
            if clasificar_prefijo_articulo(item) != "APERITIVO"
            and not normalize_text(item.get("nombre")).startswith("a p ")
        ]
        exact = coincidencias_exactas(
            articles, name, ("codigo", "id", "nombre", "nombre_normalizado")
        )
        normalized = normalize_text(name)
        alias_exact = [
            item for item in articles
            if normalized in self.aliases.aliases(item) and item not in exact
        ]
        exact.extend(alias_exact)
        if len(exact) == 1:
            candidate = self._candidate(exact[0], 1.0, unit, "Nombre o alias exacto.")
            return {
                "article_id": candidate["articulo_id"] if candidate["unidad_compatible"] else None,
                "status": (
                    "COINCIDENCIA_EXACTA_PROPUESTA"
                    if candidate["unidad_compatible"]
                    else "REVISAR_COINCIDENCIA"
                ),
                "confidence": 1.0,
                "candidates": [candidate],
            }

        candidates: list[dict[str, Any]] = []
        for article in articles:
            scores = []
            for alias in self.aliases.aliases(article):
                score = SequenceMatcher(None, normalized, alias).ratio()
                if normalized in alias or alias in normalized:
                    score = max(score, 0.88)
                scores.append(score)
            score = max(scores, default=0.0)
            if score >= 0.58:
                candidates.append(self._candidate(
                    article, score, unit,
                    "Nombre parecido; requiere elección del usuario.",
                ))
        candidates.sort(key=lambda item: item["nivel_coincidencia"], reverse=True)
        if exact:
            candidates = [
                self._candidate(item, 1.0, unit, "Hay varias coincidencias exactas.")
                for item in exact
            ]
        return {
            "article_id": None,
            "status": "REVISAR_COINCIDENCIA" if candidates else "SIN_RELACIONAR",
            "confidence": candidates[0]["nivel_coincidencia"] if candidates else 0.0,
            "candidates": candidates[:5],
        }

    @staticmethod
    def _candidate(
        article: dict[str, Any], score: float, requested_unit: str | None, reason: str
    ) -> dict[str, Any]:
        article_unit = normalizar_unidad(str(
            article.get("unidad_recetas") or article.get("unidad_base") or article.get("unidad") or ""
        ))
        compatible = ArticleCandidateFinder._units_compatible(
            normalizar_unidad(requested_unit or ""), article_unit
        )
        return {
            "articulo_id": str(article.get("codigo") or article.get("id") or ""),
            "codigo": str(article.get("codigo") or ""),
            "nombre": str(article.get("nombre") or ""),
            "categoria": str(article.get("familia") or article.get("categoria") or ""),
            "unidad": article_unit or None,
            "precio": article.get("precio"),
            "nivel_coincidencia": round(score, 4),
            "motivo": reason if compatible else f"{reason} La unidad del artículo no coincide.",
            "unidad_compatible": compatible,
        }

    @staticmethod
    def _units_compatible(requested: str, article: str) -> bool:
        if not requested or not article or requested == article:
            return True
        metric_groups = ({"kg", "g"}, {"l", "ml", "cl"})
        return any(requested in group and article in group for group in metric_groups)


class ImportDraftService:
    def __init__(self, base_dir: Path) -> None:
        self.quantities = CulinaryQuantityParser()
        self.names = IngredientTextNormalizer()
        self.articles = ArticleCandidateFinder(base_dir)

    def build(
        self, *, import_id: str, classification: str, confidence: float,
        recipes: list[dict[str, Any]], created_at: str | None = None,
    ) -> dict[str, Any]:
        now = created_at or datetime.now(timezone.utc).isoformat()
        drafts = [self._recipe(item, index) for index, item in enumerate(recipes, 1)]
        draft = ImportDraft(
            id=f"{import_id}-DRAFT",
            document_id=import_id,
            status=DraftStatus.PENDIENTE_REVISION,
            classification=classification,
            confidence=confidence,
            recipes=drafts,
            warnings=[],
            conflicts=[],
            version=1,
            created_at=now,
            updated_at=now,
        )
        self._validate(draft)
        result = draft.to_dict()
        self._validate_dict(result)
        return result

    def update(self, current: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        expected = payload.get("draft_version", payload.get("version"))
        if not isinstance(expected, int) or expected != int(current.get("version") or 0):
            raise DraftConflictError(int(current.get("version") or 0))
        candidate = deepcopy(current)
        patches = payload.get("recipes")
        if not isinstance(patches, list):
            raise DraftValidationError("El borrador debe incluir una lista de secciones.")
        by_id = {str(item.get("id")): item for item in candidate.get("recipes") or []}
        for patch in patches:
            if not isinstance(patch, dict) or str(patch.get("id") or "") not in by_id:
                raise DraftValidationError("La sección editada no pertenece al borrador.")
            target = by_id[str(patch["id"])]
            self._patch_recipe(target, patch, by_id)
        candidate["recipes"] = sorted(by_id.values(), key=lambda item: int(item.get("order") or 0))
        candidate["version"] = int(current["version"]) + 1
        candidate["draft_version"] = candidate["version"]
        candidate["status"] = DraftStatus.EN_REVISION.value
        candidate["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._validate_dict(candidate)
        return candidate

    def validate(self, draft: dict[str, Any]) -> dict[str, Any]:
        """Recalcula toda la validación desde el borrador revisado."""
        candidate = deepcopy(draft)
        self._validate_dict(candidate)
        return candidate

    def _recipe(self, raw: dict[str, Any], order: int) -> RecipeDraft:
        ingredients = [
            self._ingredient(item, order, index)
            for index, item in enumerate(raw.get("ingredientes_estructurados") or [], 1)
        ]
        duplicate = dict(raw.get("coincidencia_biblioteca") or {})
        duplicate_candidates = list(duplicate.get("candidatos") or [])
        return RecipeDraft(
            id=str(raw.get("id_origen") or f"REC-DRAFT-{order:03d}"),
            title=str(raw.get("nombre") or "").strip(),
            entity_type=RecipeEntityType.PRINCIPAL,
            parent_recipe_id=None,
            order=order,
            description="",
            ingredients=ingredients,
            procedure=[str(item) for item in raw.get("pasos") or []],
            yield_value=raw.get("rendimiento"),
            servings=raw.get("numero_raciones"),
            times={},
            temperatures=[],
            notes="",
            source_blocks=list(raw.get("bloques_origen") or []),
            confidence=0.75,
            proposed_action=(
                "ACTUALIZAR_RECETA"
                if duplicate.get("estado") == "coincidencia_exacta"
                else "CREAR_RECETA"
            ),
            duplicate_candidates=duplicate_candidates,
        )

    def _ingredient(
        self, raw: dict[str, Any], recipe_order: int, ingredient_order: int
    ) -> IngredientDraft:
        quantity_raw = str(raw.get("cantidad_texto") or "")
        quantity, issues = self.quantities.parse(quantity_raw)
        name, extracted_observation = self.names.split(raw.get("nombre_original"))
        unit_raw = str(raw.get("unidad") or "")
        unit = normalizar_unidad(unit_raw) or None
        relation = self.articles.find(name, unit)
        return IngredientDraft(
            id=f"ING-DRAFT-{recipe_order:03d}-{ingredient_order:03d}",
            original_text=" ".join(filter(None, (quantity_raw, unit_raw, str(raw.get("nombre_original") or "")))),
            quantity_raw=quantity_raw,
            quantity=quantity,
            unit_raw=unit_raw,
            unit=unit,
            name_raw=name,
            normalized_name=normalize_text(name),
            observations=str(raw.get("observaciones") or extracted_observation or ""),
            article_id=relation["article_id"],
            article_candidates=relation["candidates"],
            relation_status=relation["status"],
            confidence=relation["confidence"],
            validation_errors=issues,
        )

    def _patch_recipe(
        self, target: dict[str, Any], patch: dict[str, Any], recipes: dict[str, dict[str, Any]]
    ) -> None:
        for key in ("title", "description", "notes", "proposed_action"):
            if key in patch:
                target[key] = str(patch.get(key) or "").strip()
        for key in ("servings", "yield_value"):
            if key in patch:
                target[key] = self._number_or_none(patch.get(key))
        if target.get("proposed_action") not in VALID_ACTIONS:
            raise DraftValidationError("La acción propuesta no es válida.")
        if "entity_type" in patch:
            try:
                target["entity_type"] = RecipeEntityType(str(patch["entity_type"])).value
            except ValueError as exc:
                raise DraftValidationError("El tipo culinario no es válido.") from exc
        if "parent_recipe_id" in patch:
            parent = str(patch.get("parent_recipe_id") or "") or None
            if parent and (
                parent not in recipes
                or parent == target["id"]
                or recipes[parent].get("entity_type") != RecipeEntityType.PRINCIPAL.value
            ):
                raise DraftValidationError("La elaboración principal seleccionada no es válida.")
            target["parent_recipe_id"] = parent
        if "procedure" in patch:
            if not isinstance(patch["procedure"], list):
                raise DraftValidationError("El procedimiento debe ser una lista.")
            target["procedure"] = [str(item).strip() for item in patch["procedure"] if str(item).strip()]
        if "ingredients" in patch:
            self._patch_ingredients(target, patch["ingredients"])

    def _patch_ingredients(self, recipe: dict[str, Any], patches: Any) -> None:
        if not isinstance(patches, list):
            raise DraftValidationError("Los ingredientes deben enviarse como una lista.")
        current = {
            str(item.get("id")): item
            for item in recipe.get("ingredients") or []
            if str(item.get("id") or "")
        }
        revised: list[dict[str, Any]] = []
        used_ids: set[str] = set()
        for index, patch in enumerate(patches, 1):
            if not isinstance(patch, dict):
                raise DraftValidationError("Cada ingrediente debe ser un objeto.")
            requested_id = str(patch.get("id") or "")
            if requested_id in current:
                item = deepcopy(current[requested_id])
            elif not requested_id or requested_id.startswith("NEW-"):
                item = self._new_ingredient(recipe, index)
            else:
                raise DraftValidationError("El ingrediente editado no pertenece al borrador.")
            if item["id"] in used_ids:
                raise DraftValidationError("No se puede repetir el mismo ingrediente en el borrador.")
            used_ids.add(item["id"])
            for key in ("quantity_raw", "unit_raw", "name_raw", "observations", "relation_status"):
                if key in patch:
                    item[key] = str(patch.get(key) or "").strip()
            if item["relation_status"] not in VALID_RELATIONS:
                raise DraftValidationError("El estado de relación del ingrediente no es válido.")
            quantity, issues = self.quantities.parse(item["quantity_raw"])
            item["quantity"] = quantity
            item["unit"] = normalizar_unidad(item["unit_raw"]) or None
            item["normalized_name"] = normalize_text(item["name_raw"])
            relation = self.articles.find(item["name_raw"], item["unit"])
            item["article_candidates"] = relation["candidates"]
            item["confidence"] = relation["confidence"]
            article_id = str(patch.get("article_id") or "") or None
            if article_id:
                candidate = next(
                    (value for value in item.get("article_candidates") or []
                     if value.get("articulo_id") == article_id),
                    None,
                )
                if candidate is None:
                    raise DraftValidationError("El artículo seleccionado no es un candidato válido.")
                item["article_id"] = article_id
                item["relation_status"] = "RELACIONADO"
            elif "article_id" in patch:
                item["article_id"] = None
            item["validation_errors"] = [issue.to_dict() for issue in issues]
            revised.append(item)
        recipe["ingredients"] = revised

    @staticmethod
    def _new_ingredient(recipe: dict[str, Any], index: int) -> dict[str, Any]:
        existing = {
            str(item.get("id") or "")
            for item in recipe.get("ingredients") or []
        }
        sequence = index
        while True:
            ingredient_id = f"{recipe['id']}-ING-{sequence:03d}"
            if ingredient_id not in existing:
                break
            sequence += 1
        return {
            "id": ingredient_id,
            "original_text": "",
            "quantity_raw": "",
            "quantity": None,
            "unit_raw": "",
            "unit": None,
            "name_raw": "",
            "normalized_name": "",
            "observations": "",
            "article_id": None,
            "article_candidates": [],
            "relation_status": "SIN_RELACIONAR",
            "confidence": 0.0,
            "validation_errors": [],
        }

    def _validate(self, draft: ImportDraft) -> None:
        raw = draft.to_dict()
        self._validate_dict(raw)
        for recipe, validated in zip(draft.recipes, raw["recipes"]):
            recipe.validation_errors = [
                DraftIssue(
                    issue["code"], DraftIssueLevel(issue["level"]),
                    issue["message"], issue.get("field", ""),
                )
                for issue in validated["validation_errors"]
            ]
            for ingredient, validated_ingredient in zip(
                recipe.ingredients, validated["ingredients"]
            ):
                ingredient.validation_errors = [
                    DraftIssue(
                        issue["code"], DraftIssueLevel(issue["level"]),
                        issue["message"], issue.get("field", ""),
                    )
                    for issue in validated_ingredient["validation_errors"]
                ]

    def _validate_dict(self, draft: dict[str, Any]) -> None:
        recipes = list(draft.get("recipes") or [])
        ids = {str(item.get("id")) for item in recipes}
        for recipe in recipes:
            issues: list[dict[str, Any]] = []
            entity_type = str(recipe.get("entity_type") or "")
            active = (
                entity_type != RecipeEntityType.DESCARTAR.value
                and recipe.get("proposed_action") != "IGNORAR"
            )
            if active and not str(recipe.get("title") or "").strip():
                issues.append(DraftIssue(
                    "TITULO_VACIO", DraftIssueLevel.ERROR,
                    "La sección necesita un título.", "title",
                ).to_dict())
            if active and entity_type == RecipeEntityType.SUBELABORACION.value and recipe.get("parent_recipe_id") not in ids:
                issues.append(DraftIssue(
                    "SUBELABORACION_SIN_PRINCIPAL", DraftIssueLevel.ERROR,
                    "Selecciona la elaboración principal de esta subelaboración.", "parent_recipe_id",
                ).to_dict())
            if (
                active
                and not [item for item in recipe.get("procedure") or [] if str(item).strip()]
            ):
                issues.append(DraftIssue(
                    "PROCEDIMIENTO_VACIO", DraftIssueLevel.ERROR,
                    "El procedimiento es obligatorio antes de confirmar.", "procedure",
                ).to_dict())
            if (
                active
                and not self._is_positive_number(
                    recipe.get("servings") or recipe.get("yield_value")
                )
            ):
                issues.append(DraftIssue(
                    "RACIONES_INVALIDAS", DraftIssueLevel.ERROR,
                    "El rendimiento o número de raciones debe ser mayor que cero.", "servings",
                ).to_dict())
            if (
                active
                and not recipe.get("ingredients")
            ):
                issues.append(DraftIssue(
                    "INGREDIENTES_VACIOS", DraftIssueLevel.ERROR,
                    "Añade al menos un ingrediente antes de confirmar.", "ingredients",
                ).to_dict())
            if entity_type == RecipeEntityType.COMPONENTE.value and not (
                recipe.get("ingredients") or recipe.get("procedure")
            ):
                issues.append(DraftIssue(
                    "COMPONENTE_SIN_CONTENIDO", DraftIssueLevel.ADVERTENCIA,
                    "El componente no contiene ingredientes ni procedimiento.",
                ).to_dict())
            if entity_type == RecipeEntityType.DESCARTAR.value:
                issues.append(DraftIssue(
                    "SECCION_IGNORADA", DraftIssueLevel.SUGERENCIA,
                    "Esta sección quedará fuera de una confirmación futura.",
                ).to_dict())
                if recipe.get("proposed_action") != "IGNORAR":
                    issues.append(DraftIssue(
                        "PROPUESTA_CONTRADICTORIA", DraftIssueLevel.ADVERTENCIA,
                        "Una sección ignorada no debe conservar una acción de creación.",
                        "proposed_action",
                    ).to_dict())
            seen: set[str] = set()
            for ingredient in recipe.get("ingredients") or []:
                if not active:
                    ingredient["validation_errors"] = []
                    continue
                ingredient_issues = [
                    issue for issue in ingredient.get("validation_errors") or []
                    if issue.get("code") in {
                        "CANTIDAD_AMBIGUA", "CANTIDAD_RANGO", "CANTIDAD_APROXIMADA", "CANTIDAD_INVALIDA"
                    }
                ]
                if (
                    ingredient.get("quantity") is None
                    and not any(
                        issue.get("level") == DraftIssueLevel.ERROR.value
                        for issue in ingredient_issues
                    )
                ):
                    ingredient_issues.append(DraftIssue(
                        "CANTIDAD_SIN_RESOLVER", DraftIssueLevel.ERROR,
                        "Introduce una cantidad numérica antes de confirmar.", "quantity",
                    ).to_dict())
                unit = str(ingredient.get("unit") or "")
                if unit and unit not in {normalizar_unidad(value) for value in UNIDADES_ADMITIDAS}:
                    ingredient_issues.append(DraftIssue(
                        "UNIDAD_DESCONOCIDA", DraftIssueLevel.ADVERTENCIA,
                        f"La unidad «{unit}» no está normalizada.", "unit",
                    ).to_dict())
                normalized_name = str(
                    ingredient.get("normalized_name")
                    or normalize_text(ingredient.get("name_raw"))
                )
                ingredient["normalized_name"] = normalized_name
                if not normalized_name:
                    ingredient_issues.append(DraftIssue(
                        "INGREDIENTE_SIN_NOMBRE", DraftIssueLevel.ERROR,
                        "El nombre del ingrediente es obligatorio.", "name",
                    ).to_dict())
                if normalized_name and normalized_name in seen:
                    ingredient_issues.append(DraftIssue(
                        "INGREDIENTE_DUPLICADO", DraftIssueLevel.ADVERTENCIA,
                        "El ingrediente aparece más de una vez en la sección.", "name",
                    ).to_dict())
                seen.add(normalized_name)
                if (
                    ingredient.get("relation_status") == "RELACIONADO"
                    and not ingredient.get("article_id")
                ):
                    ingredient_issues.append(DraftIssue(
                        "ARTICULO_NO_SELECCIONADO", DraftIssueLevel.ERROR,
                        "Selecciona el artículo relacionado o deja la relación pendiente.",
                        "article_id",
                    ).to_dict())
                ingredient["validation_errors"] = ingredient_issues
            recipe["validation_errors"] = issues
        validation = self._validation_summary(recipes)
        draft["validation"] = validation
        draft["confirmation_available"] = validation["valid"]

    @staticmethod
    def _number_or_none(value: Any) -> float | None:
        try:
            return float(str(value).replace(",", ".")) if value not in {None, ""} else None
        except (TypeError, ValueError):
            return None

    @classmethod
    def _is_positive_number(cls, value: Any) -> bool:
        parsed = cls._number_or_none(value)
        return parsed is not None and parsed > 0

    @staticmethod
    def _validation_summary(recipes: list[dict[str, Any]]) -> dict[str, Any]:
        blocking: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        for recipe_index, recipe in enumerate(recipes):
            recipe_id = str(recipe.get("id") or "")
            recipe_title = str(recipe.get("title") or "Sin título")
            contextual = {
                "recipe_id": recipe_id,
                "recipe_title": recipe_title,
                "recipe_index": recipe_index,
            }
            for issue in recipe.get("validation_errors") or []:
                target = blocking if issue.get("level") == DraftIssueLevel.ERROR.value else warnings
                target.append({
                    **issue,
                    **contextual,
                    "level": (
                        "BLOQUEANTE"
                        if issue.get("level") == DraftIssueLevel.ERROR.value
                        else "ADVERTENCIA"
                    ),
                    "ingredient_id": None,
                    "ingredient_index": None,
                })
            for ingredient_index, ingredient in enumerate(recipe.get("ingredients") or []):
                for issue in ingredient.get("validation_errors") or []:
                    target = blocking if issue.get("level") == DraftIssueLevel.ERROR.value else warnings
                    target.append({
                        **issue,
                        **contextual,
                        "level": (
                            "BLOQUEANTE"
                            if issue.get("level") == DraftIssueLevel.ERROR.value
                            else "ADVERTENCIA"
                        ),
                        "ingredient_id": str(ingredient.get("id") or ""),
                        "ingredient_index": ingredient_index,
                    })
        return {
            "valid": not blocking,
            "blocking_errors": blocking,
            "warnings": warnings,
        }


class DraftConflictError(Exception):
    def __init__(self, current_version: int) -> None:
        super().__init__("El borrador cambió desde la última lectura.")
        self.current_version = current_version


class DraftValidationError(Exception):
    pass


__all__ = [
    "ArticleCandidateFinder",
    "CulinaryQuantityParser",
    "DraftConflictError",
    "DraftValidationError",
    "ImportDraftService",
    "IngredientAliasResolver",
    "IngredientTextNormalizer",
    "normalize_text",
]
