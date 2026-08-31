from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import unicodedata
from typing import Any

from SERVICIOS.articulos_catalog_read_service import ArticulosCatalogReadService
from SERVICIOS.host_ai_escandallos_read_service import HostAIEscandallosReadService


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join("".join(char for char in text if not unicodedata.combining(char)).lower().split())


@dataclass(frozen=True)
class RecipeCompletionInvestigation:
    recipe_id: str
    summary: str
    completeness: dict[str, list[dict[str, Any]]]
    procedure_proposal: str
    actions: list[dict[str, Any]]
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "summary": self.summary,
            "completeness": self.completeness,
            "procedure_proposal": self.procedure_proposal,
            "actions": self.actions,
            "data": self.data,
            "datos_reales_modificados": False,
        }


class RecipeCompletionWorkflow:
    """Investigación READ agregada para completar una receta sin mutar datos."""

    def __init__(
        self,
        base_dir: Path,
        *,
        recipes: HostAIEscandallosReadService | None = None,
        articles: ArticulosCatalogReadService | None = None,
    ) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.recipes = recipes or HostAIEscandallosReadService(self.base_dir)
        self.articles = articles or ArticulosCatalogReadService(self.base_dir)

    def investigate(self, recipe_id: str) -> RecipeCompletionInvestigation:
        response = self.recipes.consultar("detalle", escandallo_id=str(recipe_id or ""), limite=10)
        detail = response.get("escandallo") if response.get("estado") == "OK" else None
        if not isinstance(detail, dict):
            return RecipeCompletionInvestigation(
                str(recipe_id or ""), "No he podido identificar una receta concreta para revisarla.",
                {"RESUELTO": [], "FALTA": [{"campo": "receta"}], "AMBIGUO": [], "NO_VERIFICABLE": []},
                "", [], {"estado": response.get("estado") or "NO_ENCONTRADO"},
            )

        completeness: dict[str, list[dict[str, Any]]] = {
            "RESUELTO": [], "FALTA": [], "AMBIGUO": [], "NO_VERIFICABLE": [],
        }
        self._field(completeness, "nombre", detail.get("nombre"))
        self._field(completeness, "rendimiento", detail.get("rendimiento") or detail.get("raciones"))
        self._field(completeness, "ingredientes", detail.get("ingredientes"))
        self._field(completeness, "escandallo", detail.get("tiene_escandallo"))
        self._field(completeness, "tiempos", detail.get("tiempo_total") or detail.get("tiempo_activo"))
        self._field(completeness, "conservación", detail.get("conservacion"))
        self._field(completeness, "alérgenos", detail.get("alergenos"))
        self._field(completeness, "dependencias", self._dependencies(detail))

        unresolved: list[dict[str, Any]] = []
        missing_prices: list[str] = []
        actions: list[dict[str, Any]] = []
        for ingredient_index, ingredient in enumerate(list(detail.get("ingredientes") or [])):
            if not isinstance(ingredient, dict):
                continue
            name = str(ingredient.get("nombre_articulo") or ingredient.get("nombre_original") or "").strip()
            article_id = str(ingredient.get("articulo_id") or "").strip()
            relation = str(ingredient.get("estado_relacion") or "").upper()
            if article_id or relation in {"RELACIONADO", "RESUELTO"}:
                completeness["RESUELTO"].append({"campo": "relación de ingrediente", "ingrediente": name, "articulo_id": article_id})
                article = self._article(article_id) if article_id else {}
                if article_id and article.get("precio") in (None, ""):
                    missing_prices.append(str(article.get("nombre") or name or article_id))
            else:
                resolution = self._resolve_article(name)
                unresolved.append({"ingrediente": name, **resolution})
                state = resolution["state"]
                if state in {"EXACT", "HIGH_CONFIDENCE"}:
                    completeness["FALTA"].append({"campo": "confirmación de relación", "ingrediente": name, "candidato": resolution.get("candidate")})
                    candidate = dict(resolution.get("candidate") or {})
                    actions.append({
                        "action_id": "PREVIEW_INGREDIENT_RELATION",
                        "recipe_id": str(detail.get("id") or detail.get("codigo") or ""),
                        "ingredient_index": ingredient_index,
                        "article_id": str(candidate.get("id") or ""),
                        "label": f"Relacionar {name}",
                    })
                    if candidate.get("precio") in (None, ""):
                        missing_prices.append(str(candidate.get("nombre") or name))
                elif state == "AMBIGUOUS":
                    completeness["AMBIGUO"].append({"campo": "relación de ingrediente", "ingrediente": name, "candidatos": resolution.get("candidates", [])})
                else:
                    completeness["FALTA"].append({"campo": "relación de ingrediente", "ingrediente": name})

            cost_state = str(ingredient.get("estado_coste") or "").upper()
            if cost_state in {"SIN_PRECIO", "SIN_COSTE"}:
                missing_prices.append(name or article_id)
            if cost_state == "SIN_CONVERSION":
                completeness["NO_VERIFICABLE"].append({"campo": "conversión", "ingrediente": name})

        procedure = str(detail.get("procedimiento") or "").strip()
        proposal = ""
        if procedure:
            completeness["RESUELTO"].append({"campo": "procedimiento"})
        else:
            completeness["FALTA"].append({"campo": "procedimiento"})
            proposal = self._procedure_proposal(detail)
            if self._is_library_recipe(detail):
                actions.append({"action_id": "PREVIEW_RECIPE_PROCEDURE", "recipe_id": str(detail.get("id") or detail.get("codigo") or ""), "label": "Revisar propuesta de procedimiento"})
            else:
                completeness["NO_VERIFICABLE"].append({"campo": "guardar procedimiento", "motivo": "receta heredada sin ruta de escritura canónica"})

        for name in dict.fromkeys(value for value in missing_prices if value):
            completeness["FALTA"].append({"campo": "precio real", "articulo": name, "estado_precio": "PRECIO_DESCONOCIDO"})

        exact = sum(item["state"] in {"EXACT", "HIGH_CONFIDENCE"} for item in unresolved)
        ambiguous = sum(item["state"] == "AMBIGUOUS" for item in unresolved)
        summary = self._summary(detail, unresolved, missing_prices, bool(proposal), exact, ambiguous)
        return RecipeCompletionInvestigation(
            str(detail.get("id") or detail.get("codigo") or recipe_id), summary, completeness, proposal, actions,
            {"detail": detail, "ingredient_resolutions": unresolved, "missing_prices": list(dict.fromkeys(missing_prices))},
        )

    @staticmethod
    def _field(result: dict[str, list[dict[str, Any]]], field: str, value: Any) -> None:
        (result["RESUELTO"] if value not in (None, "", [], False) else result["FALTA"]).append({"campo": field})

    @staticmethod
    def _dependencies(detail: dict[str, Any]) -> list[Any]:
        return [item for item in list(detail.get("ingredientes") or []) if item.get("tipo_componente") == "ELABORACION" or item.get("escandallo_hijo_id")]

    def _article(self, article_id: str) -> dict[str, Any]:
        response = self.articles.obtener(article_id)
        return dict(response.get("articulo") or {}) if response.get("ok") else {}

    def _resolve_article(self, ingredient: str) -> dict[str, Any]:
        query = self.articles.listar({"q": ingredient, "page": 1, "page_size": 100})
        candidates = [dict(item) for item in list((query.get("catalogo") or {}).get("items") or [])]
        needle = _norm(ingredient)
        exact = [item for item in candidates if _norm(item.get("nombre")) == needle or _norm(item.get("codigo")) == needle]
        if len(exact) == 1:
            return {"state": "EXACT", "candidate": exact[0], "candidates": exact}
        token_matches = [item for item in candidates if set(needle.split()) <= set(_norm(item.get("nombre")).split())]
        if len(token_matches) == 1:
            return {"state": "HIGH_CONFIDENCE", "candidate": token_matches[0], "candidates": token_matches}
        if candidates:
            return {"state": "AMBIGUOUS", "candidates": candidates[:5]}
        return {"state": "NOT_FOUND", "candidates": []}

    @staticmethod
    def _procedure_proposal(detail: dict[str, Any]) -> str:
        ingredients = [str(item.get("nombre_articulo") or item.get("nombre_original") or "ingrediente").strip() for item in list(detail.get("ingredientes") or [])]
        base = ", ".join(item for item in ingredients if item) or "los ingredientes registrados"
        return (
            "Propuesta de IA, no registrada: preparar y pesar " + base + ". "
            "Organizar la mise en place, elaborar respetando las cantidades registradas y verificar el punto antes del servicio. "
            "Revisar tiempos, temperaturas, conservación y alérgenos con el responsable antes de guardarla."
        )

    @staticmethod
    def _is_library_recipe(detail: dict[str, Any]) -> bool:
        return str(detail.get("id") or "").upper().startswith("REC601-")

    @staticmethod
    def _summary(detail: dict[str, Any], unresolved: list[dict[str, Any]], prices: list[str], procedure: bool, exact: int, ambiguous: int) -> str:
        parts = [f"He revisado {detail.get('nombre') or 'la receta'}."]
        if procedure:
            parts.append("No tiene procedimiento registrado; he preparado una propuesta de IA para revisarla antes de guardarla.")
        if exact:
            parts.append(f"He encontrado {exact} relación(es) de ingrediente que puedo preparar para confirmación.")
        if ambiguous:
            parts.append(f"Hay {ambiguous} ingrediente(s) con varias opciones y necesito que me indiques cuál utilizas.")
        if prices:
            parts.append("Para completar el coste falta el precio real de " + ", ".join(dict.fromkeys(prices)) + ".")
        if not unresolved and not prices and not procedure:
            parts.append("Los datos técnicos disponibles no muestran una incidencia inmediata.")
        return " ".join(parts)


__all__ = ["RecipeCompletionInvestigation", "RecipeCompletionWorkflow"]
