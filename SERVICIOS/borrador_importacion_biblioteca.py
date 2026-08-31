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
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos
from SERVICIOS.schema_escandallos_555a import UNIDADES_ADMITIDAS, normalizar_unidad
from SERVICIOS.utilidades_importador_i135 import coincidencias_exactas


FRACTIONS = {"¼": 0.25, "½": 0.5, "¾": 0.75}
APPROXIMATE_QUANTITIES = {"c/s", "al gusto", "una pizca", "pizca"}
VALID_ACTIONS = {
    "CREAR_ELABORACION", "CREAR_RECETA", "ACTUALIZAR_ELABORACION",
    "ACTUALIZAR_RECETA", "CREAR_SUBELABORACION", "MANTENER_COMPONENTE", "IGNORAR",
    "REUTILIZAR_EXISTENTE", "REQUIERE_REVISION", "SIN_CAMBIOS",
}
VALID_RELATIONS = {
    "RELACIONADO", "COINCIDENCIA_EXACTA_PROPUESTA", "REVISAR_COINCIDENCIA",
    "SIN_RELACIONAR", "CREAR_ARTICULO_PROPUESTO", "IGNORADO",
}


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def normalize_culinary_name(value: Any) -> str:
    """Conservative linguistic key; equivalence still requires recipe structure."""
    stopwords = {"de", "del", "la", "el", "las", "los", "una", "un"}
    return " ".join(token for token in normalize_text(value).split() if token not in stopwords)


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
        self.recipes = RepositorioBibliotecaRecetas601(base_dir)
        self.aliases = IngredientAliasResolver()

    def find(
        self, name: str, unit: str | None, imported: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        articles = [
            item for item in self.catalog.listar_productos(incluir_archivados=False)
            if clasificar_prefijo_articulo(item) != "APERITIVO"
            and not normalize_text(item.get("nombre")).startswith("a p ")
        ]
        source = imported or {}
        imported_id = normalize_text(
            source.get("article_id") or source.get("articulo_id")
            or source.get("codigo") or source.get("id_origen")
        )
        if imported_id:
            identified = [item for item in articles if imported_id in {
                normalize_text(item.get("codigo")), normalize_text(item.get("id")),
                normalize_text(item.get("id_interno")),
            } - {""}]
            if len(identified) == 1:
                candidate = self._candidate(
                    identified[0], 1.0, unit, "Identificador canónico validado."
                )
                return self._resolved_or_review(candidate, "IDENTIFICADOR_CANONICO")

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
            return self._resolved_or_review(candidate, "NOMBRE_ALIAS_EXACTO")

        learned_ids = self._learned_article_ids(normalized)
        learned = [item for item in articles if normalize_text(
            item.get("codigo") or item.get("id") or item.get("id_interno")
        ) in learned_ids]
        if len(learned) == 1:
            candidate = self._candidate(
                learned[0], 1.0, unit,
                "Relación ingrediente-artículo ya confirmada en Biblioteca.",
            )
            return self._resolved_or_review(candidate, "RELACION_HISTORICA_CONFIRMADA")

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
    def _resolved_or_review(candidate: dict[str, Any], evidence: str) -> dict[str, Any]:
        compatible = bool(candidate["unidad_compatible"])
        candidate["evidencia_identidad"] = evidence
        return {
            "article_id": candidate["articulo_id"] if compatible else None,
            "status": "COINCIDENCIA_EXACTA_PROPUESTA" if compatible else "REVISAR_COINCIDENCIA",
            "confidence": 1.0,
            "candidates": [candidate],
            "evidencia_identidad": evidence,
        }

    def _learned_article_ids(self, normalized_name: str) -> set[str]:
        if not normalized_name:
            return set()
        learned: set[str] = set()
        for recipe in self.recipes.listar(incluir_archivadas=False):
            for ingredient in recipe.get("ingredientes_estructurados") or []:
                if not isinstance(ingredient, dict):
                    continue
                ingredient_name = normalize_text(
                    ingredient.get("nombre_original") or ingredient.get("nombre")
                )
                article_id = normalize_text(
                    ingredient.get("article_id") or ingredient.get("articulo_id")
                )
                if ingredient_name == normalized_name and article_id:
                    learned.add(article_id)
        return learned

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


class CanonicalRecipeMatcher:
    """Compara el documento con Biblioteca sin convertir el nombre en autoridad."""

    ALIAS_FIELDS = ("alias", "aliases", "variantes", "nombres_alternativos")

    def __init__(self, base_dir: Path) -> None:
        self.repository = RepositorioBibliotecaRecetas601(base_dir)
        self.cost_repository = RepositorioEscandallos(
            Path(base_dir) / "DATOS" / "db" / "escandallos_canonicos.json"
        )

    def match(self, imported: dict[str, Any]) -> dict[str, Any]:
        imported_name = normalize_text(imported.get("nombre"))
        imported_semantic_name = normalize_culinary_name(imported.get("nombre"))
        imported_id = normalize_text(
            imported.get("receta_id") or imported.get("elaboracion_id")
            or imported.get("codigo") or imported.get("id_origen")
        )
        candidates: list[dict[str, Any]] = []
        for existing in self.repository.listar(incluir_archivadas=False):
            identifiers = {
                normalize_text(existing.get("id")), normalize_text(existing.get("codigo"))
            } - {""}
            names = {normalize_text(existing.get("nombre"))} | self._aliases(existing)
            id_match = bool(imported_id and imported_id in identifiers)
            name_match = bool(imported_name and imported_name in names)
            semantic_match = bool(imported_semantic_name and imported_semantic_name in {
                normalize_culinary_name(name) for name in names
            })
            linguistic_match = semantic_match or any(
                self._names_linguistically_related(imported_semantic_name, normalize_culinary_name(name))
                for name in names
            )
            if not id_match and not name_match and not linguistic_match:
                continue
            candidate = self._candidate(imported, existing, id_match=id_match)
            candidate["coincidencia_linguistica"] = linguistic_match and not name_match
            candidates.append(candidate)

        if not candidates:
            cost_candidates = self._cost_evidence(imported)
            if cost_candidates:
                return {
                    "estado": "EXISTE_EN_LEGACY_SIN_CANONICALIZAR",
                    "accion": "REQUIERE_REVISION",
                    "motivo": (
                        "Existe un escandallo con identidad compatible, pero no una receta "
                        "canónica que pueda reutilizarse automáticamente."
                    ),
                    "candidatos": cost_candidates,
                }
            return {"estado": "nueva_entidad", "accion": "CREAR_NUEVA", "candidatos": []}
        if len(candidates) > 1:
            return {
                "estado": "coincidencia_ambigua", "accion": "REQUIERE_REVISION",
                "motivo": "Hay varias entidades canónicas compatibles por identificador, nombre o alias.",
                "candidatos": candidates,
            }
        candidate = candidates[0]
        if candidate["identificador_coincide"] or candidate["estructura_compatible"]:
            return {
                "estado": "coincidencia_canonica", "accion": "REUTILIZAR_EXISTENTE",
                "motivo": candidate["motivo"], "candidatos": candidates,
                "entidad_existente_id": candidate["id"],
                "diferencias": candidate["diferencias"],
            }
        return {
            "estado": "posible_duplicado", "accion": "REQUIERE_REVISION",
            "motivo": "El nombre coincide, pero la estructura no aporta evidencia suficiente para vincular.",
            "candidatos": candidates,
        }

    @staticmethod
    def _names_linguistically_related(left: str, right: str) -> bool:
        if not left or not right:
            return False
        left_tokens, right_tokens = set(left.split()), set(right.split())
        if not left_tokens or not right_tokens:
            return False
        generic = {"salsa", "crema", "base", "caldo", "pure", "plato", "receta"}
        shared_specific = (left_tokens & right_tokens) - generic
        contained = left_tokens <= right_tokens or right_tokens <= left_tokens
        return bool(shared_specific and (
            contained or SequenceMatcher(None, left, right).ratio() >= 0.78
        ))

    def _cost_evidence(self, imported: dict[str, Any]) -> list[dict[str, Any]]:
        imported_name = normalize_culinary_name(imported.get("nombre"))
        imported_ingredients = self._ingredient_keys(imported)
        candidates: list[dict[str, Any]] = []
        try:
            cost_sheets = self.cost_repository.listar()
        except (OSError, ValueError, TypeError):
            return []
        for cost_sheet in cost_sheets:
            recipe = cost_sheet.receta
            existing_name = normalize_culinary_name(recipe.nombre)
            if imported_name != existing_name and not self._names_linguistically_related(
                imported_name, existing_name
            ):
                continue
            existing_ingredients = {
                normalize_text(ingredient.nombre) for ingredient in recipe.ingredientes
                if normalize_text(ingredient.nombre)
            }
            overlap = (
                len(imported_ingredients & existing_ingredients)
                / len(imported_ingredients | existing_ingredients)
                if imported_ingredients and existing_ingredients else 0.0
            )
            candidates.append({
                "id": str(recipe.codigo or ""), "codigo": str(recipe.codigo or ""),
                "nombre": str(recipe.nombre or ""), "tipo": "ESCANDALLO_SIN_RECETA_CANONICA",
                "estado_identidad": "EXISTE_EN_LEGACY_SIN_CANONICALIZAR",
                "identificador_coincide": False, "estructura_compatible": False,
                "coincidencia_ingredientes": round(overlap, 4),
                "ingredientes_importados": len(imported_ingredients),
                "ingredientes_existentes": len(existing_ingredients),
                "motivo": "Escandallo canónico existente sin receta Biblioteca reutilizable.",
                "diferencias": [], "coincidencia_linguistica": imported_name != existing_name,
            })
        return candidates

    def _candidate(
        self, imported: dict[str, Any], existing: dict[str, Any], *, id_match: bool
    ) -> dict[str, Any]:
        imported_ingredients = self._ingredient_keys(imported)
        existing_ingredients = self._ingredient_keys(existing)
        overlap = 0.0
        if imported_ingredients and existing_ingredients:
            overlap = len(imported_ingredients & existing_ingredients) / len(
                imported_ingredients | existing_ingredients
            )
        structure_compatible = bool(imported_ingredients and existing_ingredients and overlap >= 0.8)
        differences = self._differences(imported, existing, imported_ingredients, existing_ingredients)
        return {
            "id": str(existing.get("id") or existing.get("codigo") or ""),
            "codigo": str(existing.get("codigo") or ""),
            "nombre": str(existing.get("nombre") or ""),
            "tipo": str(existing.get("tipo") or ""),
            "identificador_coincide": id_match,
            "estructura_compatible": structure_compatible,
            "coincidencia_ingredientes": round(overlap, 4),
            "ingredientes_importados": len(imported_ingredients),
            "ingredientes_existentes": len(existing_ingredients),
            "motivo": (
                "Identificador canónico validado."
                if id_match else "Nombre o alias y estructura de ingredientes compatibles."
            ),
            "diferencias": differences,
        }

    @classmethod
    def _aliases(cls, recipe: dict[str, Any]) -> set[str]:
        aliases: set[str] = set()
        for field in cls.ALIAS_FIELDS:
            raw = recipe.get(field)
            if isinstance(raw, list):
                aliases.update(normalize_text(item) for item in raw)
            elif raw:
                aliases.add(normalize_text(raw))
        return aliases - {""}

    @staticmethod
    def _ingredient_keys(recipe: dict[str, Any]) -> set[str]:
        keys: set[str] = set()
        for item in recipe.get("ingredientes_estructurados") or []:
            if not isinstance(item, dict):
                continue
            key = normalize_text(
                item.get("nombre_original") or item.get("nombre")
                or item.get("article_id") or item.get("elaboracion_id")
            )
            if key:
                keys.add(key)
        if not keys:
            keys.update(
                normalize_text(item) for item in recipe.get("ingredientes") or []
                if normalize_text(item)
            )
        return keys

    @staticmethod
    def _differences(
        imported: dict[str, Any], existing: dict[str, Any],
        imported_ingredients: set[str], existing_ingredients: set[str],
    ) -> list[dict[str, Any]]:
        differences: list[dict[str, Any]] = []
        comparisons = (
            ("procedimiento", imported.get("pasos") or [], existing.get("elaboracion") or ""),
            ("rendimiento", imported.get("rendimiento") or imported.get("numero_raciones"), existing.get("numero_raciones")),
        )
        for field, imported_value, existing_value in comparisons:
            if imported_value and existing_value and normalize_text(imported_value) != normalize_text(existing_value):
                differences.append({"campo": field, "actual": existing_value, "importado": imported_value})
        if imported_ingredients != existing_ingredients:
            differences.append({
                "campo": "ingredientes", "actual": sorted(existing_ingredients),
                "importado": sorted(imported_ingredients),
            })
        return differences


class ImportDraftService:
    def __init__(self, base_dir: Path, *, initialize_matchers: bool = True) -> None:
        self.base_dir = Path(base_dir)
        self.validate_menu_references = initialize_matchers
        self.quantities = CulinaryQuantityParser()
        self.names = IngredientTextNormalizer()
        self.articles = ArticleCandidateFinder(base_dir) if initialize_matchers else None
        self.recipes = CanonicalRecipeMatcher(base_dir) if initialize_matchers else None

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
        if "variant_decisions" in payload:
            decisions = payload.get("variant_decisions")
            if not isinstance(decisions, list):
                raise DraftValidationError("Las decisiones de variantes deben ser una lista.")
            known_groups = {
                str(item.get("group_id") or "")
                for item in candidate.get("variant_decisions") or []
            }
            revised_decisions: list[dict[str, str]] = []
            seen_groups: set[str] = set()
            for item in decisions:
                group_id = str((item or {}).get("group_id") or "") if isinstance(item, dict) else ""
                decision = str((item or {}).get("decision") or "") if isinstance(item, dict) else ""
                if not group_id or group_id not in known_groups or group_id in seen_groups:
                    raise DraftValidationError("El grupo de variantes no pertenece al borrador.")
                if decision not in {"MISMA_RECETA", "RECETAS_DIFERENTES", "PENDIENTE"}:
                    raise DraftValidationError("La decisiÃ³n de variantes no es vÃ¡lida.")
                seen_groups.add(group_id)
                revised_decisions.append({"group_id": group_id, "decision": decision})
            if seen_groups != known_groups:
                raise DraftValidationError("Deben conservarse todos los grupos de variantes del borrador.")
            candidate["variant_decisions"] = revised_decisions
        if "article_decisions" in payload:
            decisions = payload.get("article_decisions")
            if not isinstance(decisions, list):
                raise DraftValidationError("Las decisiones de artículos deben ser una lista.")
            current_decisions = candidate.get("article_decisions") or []
            known_ids = {str(item.get("article_draft_id") or "") for item in current_decisions}
            catalog_articles = {
                str(item.get("id") or ""): item
                for item in (candidate.get("catalogo") or {}).get("articulos") or []
            }
            revised: list[dict[str, Any]] = []
            seen: set[str] = set()
            allowed = {"REUTILIZAR_ARTICULO", "NO_ARTICULO_COMPRA", "ES_ELABORACION", "PRODUCTO_VENDIBLE", "IGNORAR", "PENDIENTE"}
            for item in decisions:
                article_draft_id = str((item or {}).get("article_draft_id") or "") if isinstance(item, dict) else ""
                decision = str((item or {}).get("decision") or "") if isinstance(item, dict) else ""
                article_id = (str(item.get("article_id") or "") or None) if isinstance(item, dict) else None
                if article_draft_id not in known_ids or article_draft_id in seen:
                    raise DraftValidationError("El artículo revisado no pertenece al borrador.")
                if decision not in allowed:
                    raise DraftValidationError("La decisión de artículo no es válida.")
                candidates = catalog_articles.get(article_draft_id, {}).get("candidatos") or []
                candidate_ids = {str(value.get("article_id") or value.get("articulo_id") or "") for value in candidates}
                current_id = str(catalog_articles.get(article_draft_id, {}).get("article_id") or "")
                if decision == "REUTILIZAR_ARTICULO" and (not article_id or article_id not in candidate_ids | {current_id}):
                    raise DraftValidationError("El artículo seleccionado no es un candidato canónico válido.")
                seen.add(article_draft_id)
                revised.append({"article_draft_id": article_draft_id, "decision": decision, "article_id": article_id})
            if seen != known_ids:
                raise DraftValidationError("Deben conservarse todas las decisiones de artículos del borrador.")
            candidate["article_decisions"] = revised
        if "menu_decisions" in payload:
            decisions = payload.get("menu_decisions")
            if not isinstance(decisions, list):
                raise DraftValidationError("Las decisiones de menús deben ser una lista.")
            known_menu_ids = {
                f"MENU-DRAFT-{index:03d}" for index, _ in enumerate(candidate.get("menus") or [], 1)
            }
            revised_menus: list[dict[str, Any]] = []
            seen_menus: set[str] = set()
            canonical_recipes = {
                str(item.get("id") or item.get("codigo") or "")
                for item in self.recipes.repository.listar(incluir_archivadas=False)
            } if self.validate_menu_references and self.recipes is not None else set()
            canonical_articles = {
                str(item.get("codigo") or item.get("id") or "")
                for item in self.articles.catalog.listar_productos(incluir_archivados=False)
            } if self.validate_menu_references and self.articles is not None else set()
            for item in decisions:
                menu_id = str((item or {}).get("menu_draft_id") or "") if isinstance(item, dict) else ""
                decision = str((item or {}).get("decision") or "PENDIENTE") if isinstance(item, dict) else ""
                if menu_id not in known_menu_ids or menu_id in seen_menus:
                    raise DraftValidationError("El menú revisado no pertenece al borrador.")
                if decision not in {"PENDIENTE", "CREAR_MENU", "REUTILIZAR_MENU", "EXCLUIR_MENU_DOCUMENTAL"}:
                    raise DraftValidationError("La decisión de menú no es válida.")
                final_name = str((item or {}).get("nombre_final") or "").strip()
                if not final_name or len(final_name) > 180:
                    raise DraftValidationError("El nombre final del menú es obligatorio y debe tener como máximo 180 caracteres.")
                line_decisions = item.get("line_decisions") or []
                if not isinstance(line_decisions, list):
                    raise DraftValidationError("Las decisiones de líneas de menú deben ser una lista.")
                revised_lines: list[dict[str, Any]] = []
                seen_lines: set[int] = set()
                raw_menu = (candidate.get("menus") or [])[int(menu_id.rsplit("-", 1)[-1]) - 1]
                max_line = len(raw_menu.get("componentes") or [])
                for line in line_decisions:
                    line_index = int((line or {}).get("line_index") or 0)
                    line_decision = str((line or {}).get("decision") or "PENDIENTE")
                    if line_index < 1 or line_index > max_line or line_index in seen_lines:
                        raise DraftValidationError("La línea revisada no pertenece al menú.")
                    if line_decision not in {"PENDIENTE", "EXCLUIR", "USAR_REFERENCIA"}:
                        raise DraftValidationError("La decisión de línea de menú no es válida.")
                    reference = str((line or {}).get("referencia") or "") or None
                    reference_type = str((line or {}).get("tipo_referencia") or "") or None
                    if line_decision == "USAR_REFERENCIA" and (
                        reference_type not in {"RECETA", "PRODUCTO"} or not reference
                        or not re.fullmatch(r"(?:REC601-\d+|ART\d+)", reference)
                    ):
                        raise DraftValidationError("La línea requiere una referencia canónica válida.")
                    if line_decision == "USAR_REFERENCIA" and self.validate_menu_references:
                        known = canonical_recipes if reference_type == "RECETA" else canonical_articles
                        if reference not in known:
                            raise DraftValidationError("La referencia elegida no existe en la Biblioteca canónica.")
                    seen_lines.add(line_index)
                    revised_lines.append({"line_index": line_index, "decision": line_decision, "tipo_referencia": reference_type, "referencia": reference})
                seen_menus.add(menu_id)
                revised_menus.append({"menu_draft_id": menu_id, "decision": decision, "nombre_final": final_name, "menu_id": item.get("menu_id"), "line_decisions": revised_lines})
            candidate["menu_decisions"] = revised_menus
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
        if self.recipes is None:
            raise RuntimeError("El matching de recetas no está disponible en modo validación.")
        duplicate = self.recipes.match(raw)
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
            proposed_action="REQUIERE_REVISION" if raw.get("posible_variante") else {
                "REUTILIZAR_EXISTENTE": "REUTILIZAR_EXISTENTE",
                "REQUIERE_REVISION": "REQUIERE_REVISION",
            }.get(str(duplicate.get("accion") or ""), "CREAR_RECETA"),
            duplicate_candidates=duplicate_candidates,
            identity_decision=None,
        )

    def _ingredient(
        self, raw: dict[str, Any], recipe_order: int, ingredient_order: int
    ) -> IngredientDraft:
        quantity_raw = str(raw.get("cantidad_texto") or "")
        quantity, issues = self.quantities.parse(quantity_raw)
        name, extracted_observation = self.names.split(raw.get("nombre_original"))
        unit_raw = str(raw.get("unidad") or "")
        unit = normalizar_unidad(unit_raw) or None
        if self.articles is None:
            raise RuntimeError("El matching de artículos no está disponible en modo validación.")
        relation = self.articles.find(name, unit, raw)
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
            source_trace=dict(raw.get("trazabilidad") or {}),
            validation_errors=issues,
        )

    def _patch_recipe(
        self, target: dict[str, Any], patch: dict[str, Any], recipes: dict[str, dict[str, Any]]
    ) -> None:
        for key in ("title", "description", "notes", "proposed_action", "identity_decision"):
            if key in patch:
                target[key] = str(patch.get(key) or "").strip()
        for key in ("servings", "yield_value"):
            if key in patch:
                target[key] = self._number_or_none(patch.get(key))
        if target.get("proposed_action") not in VALID_ACTIONS:
            raise DraftValidationError("La acción propuesta no es válida.")
        if target.get("identity_decision") not in {
            None, "", "MISMA_RECETA", "VARIANTE", "RECETA_NUEVA", "PENDIENTE",
        }:
            raise DraftValidationError("La decisión de identidad no es válida.")
        if "selected_canonical_recipe_id" in patch:
            selected_id = str(patch.get("selected_canonical_recipe_id") or "").strip()
            if selected_id:
                canonical = self.recipes.repository.obtener(selected_id) if self.recipes else None
                if not selected_id.startswith("REC601-") or canonical is None:
                    raise DraftValidationError("La receta seleccionada no existe en la Biblioteca canónica.")
                target["selected_canonical_recipe_id"] = selected_id
                selected_candidate = {
                    "id": selected_id,
                    "recipe_id": selected_id,
                    "nombre": canonical.get("nombre") or canonical.get("title") or selected_id,
                    "estado": canonical.get("estado"),
                    "ingredientes": len(canonical.get("ingredientes") or []),
                    "procedencia": canonical.get("procedencia") or canonical.get("origen"),
                }
                remaining = [
                    item for item in (target.get("duplicate_candidates") or [])
                    if str(item.get("id") or item.get("recipe_id") or "") != selected_id
                ]
                target["duplicate_candidates"] = [selected_candidate, *remaining]
            else:
                target["selected_canonical_recipe_id"] = None
        if target.get("proposed_action") == "REUTILIZAR_EXISTENTE":
            candidates = target.get("duplicate_candidates") or []
            candidate_id = str(target.get("selected_canonical_recipe_id") or (candidates[0] if candidates else {}).get("id") or "")
            canonical = self.recipes.repository.obtener(candidate_id) if self.recipes and candidate_id else None
            if not candidate_id.startswith("REC601-") or canonical is None:
                target["identity_decision"] = "PENDIENTE"
                target["proposed_action"] = "REQUIERE_REVISION"
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
            if self.articles is None:
                raise RuntimeError("El matching de artículos no está disponible en modo validación.")
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
                and recipe.get("proposed_action") not in {
                    "IGNORAR", "REUTILIZAR_EXISTENTE", "SIN_CAMBIOS"
                }
            )
            if recipe.get("proposed_action") == "REQUIERE_REVISION":
                issues.append(DraftIssue(
                    "RECETA_REQUIERE_REVISION", DraftIssueLevel.ERROR,
                    "La coincidencia con Biblioteca debe revisarse antes de confirmar.",
                    "proposed_action",
                ).to_dict())
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
                    "PROCEDIMIENTO_PENDIENTE", DraftIssueLevel.ADVERTENCIA,
                    "Procedimiento no informado; la receta se importará pendiente de completar.", "procedure",
                ).to_dict())
            if (
                active
                and not self._is_positive_number(
                    recipe.get("servings") or recipe.get("yield_value")
                )
            ):
                issues.append(DraftIssue(
                    "RENDIMIENTO_PENDIENTE", DraftIssueLevel.ADVERTENCIA,
                    "Rendimiento no informado; la receta se importará pendiente de completar.", "servings",
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
        for decision in draft.get("variant_decisions") or []:
            if decision.get("decision") == "PENDIENTE":
                validation["blocking_errors"].append({
                    "code": "VARIANTE_REQUIERE_DECISION", "level": "BLOQUEANTE",
                    "message": "El grupo de variantes sigue pendiente de revisiÃ³n.",
                    "field": "variant_decisions", "recipe_id": "",
                    "recipe_title": str(decision.get("group_id") or "Grupo de variantes"),
                    "recipe_index": -1, "ingredient_id": None, "ingredient_index": None,
                })
        validation["valid"] = not validation["blocking_errors"]
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
