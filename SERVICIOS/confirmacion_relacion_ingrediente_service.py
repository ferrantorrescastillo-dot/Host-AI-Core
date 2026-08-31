from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from SERVICIOS.articulos_catalog_read_service import ArticulosCatalogReadService
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos


class ErrorConfirmacionRelacionIngrediente(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class ConfirmacionRelacionIngredienteService:
    """Relaciona un ingrediente existente tras preview explícito, sin crear artículos."""

    REQUIRED_SCOPE = "recetas:write"

    def __init__(self, base_dir: Path, *, repository: RepositorioEscandallos | None = None, articles: ArticulosCatalogReadService | None = None) -> None:
        base = Path(base_dir).resolve()
        self.repository = repository or RepositorioEscandallos(base / "DATOS" / "db" / "escandallos_canonicos.json")
        self.articles = articles or ArticulosCatalogReadService(base)

    def preview(self, *, recipe_id: str, ingredient_index: int, article_id: str, context: AuthorizedExecutionContext) -> dict[str, Any]:
        self._authorize(context)
        recipe = self._recipe(recipe_id)
        ingredient = self._ingredient(recipe, ingredient_index)
        article = self._article(article_id)
        current = str(ingredient.articulo_id or "")
        fingerprint = self._fingerprint(recipe)
        unchanged = current == str(article["id"])
        return {
            "ok": True, "estado": "SIN_CAMBIOS" if unchanged else "LISTO_PARA_CONFIRMAR",
            "recipe_id": recipe.receta.codigo, "ingredient_index": ingredient_index,
            "ingrediente": ingredient.nombre, "articulo_actual": current or None,
            "articulo_propuesto": {"id": article["id"], "nombre": article["nombre"], "unidad": article.get("unidad")},
            "version_esperada": fingerprint,
            "preview_token": self._token(recipe.receta.codigo, ingredient_index, article["id"], fingerprint),
            "requiere_confirmacion": not unchanged, "datos_reales_modificados": False,
        }

    def confirm(self, *, recipe_id: str, ingredient_index: int, article_id: str, preview_token: str, context: AuthorizedExecutionContext) -> dict[str, Any]:
        preview = self.preview(recipe_id=recipe_id, ingredient_index=ingredient_index, article_id=article_id, context=context)
        if not preview_token or preview_token != preview["preview_token"]:
            raise ErrorConfirmacionRelacionIngrediente("stale_or_invalid_preview", "La receta o el ingrediente han cambiado desde la vista previa.")
        if preview["estado"] == "SIN_CAMBIOS":
            return {**preview, "idempotente": True, "datos_reales_modificados": False}
        recipe = self._recipe(recipe_id)
        ingredient = self._ingredient(recipe, ingredient_index)
        ingredient.articulo_id = str(article_id)
        ingredient.codigo = str(article_id)
        ingredient.metadata = {**dict(ingredient.metadata or {}), "estado_relacion": "RELACIONADO", "origen_relacion": "CONFIRMACION_USUARIO"}
        action = self.repository.upsert(recipe)
        return {"ok": True, "estado": "CONFIRMADO", "accion": action, "recipe_id": recipe.receta.codigo, "ingredient_index": ingredient_index, "articulo_id": str(article_id), "idempotente": False, "datos_reales_modificados": True}

    def _authorize(self, context: AuthorizedExecutionContext) -> None:
        valid, _reason = context.validate() if isinstance(context, AuthorizedExecutionContext) else (False, "")
        if not valid or self.REQUIRED_SCOPE not in context.scopes:
            raise ErrorConfirmacionRelacionIngrediente("unauthorized", "El actor no está autorizado para relacionar ingredientes.")

    def _recipe(self, recipe_id: str):
        key = str(recipe_id or "").strip().casefold()
        for item in self.repository.listar():
            if key == str(item.receta.codigo or "").casefold():
                return item
        raise ErrorConfirmacionRelacionIngrediente("recipe_not_found", "La receta canónica no existe.")

    @staticmethod
    def _ingredient(recipe: Any, index: int):
        if not isinstance(index, int) or index < 0 or index >= len(recipe.receta.ingredientes):
            raise ErrorConfirmacionRelacionIngrediente("ingredient_not_found", "El ingrediente ya no existe en esa posición.")
        return recipe.receta.ingredientes[index]

    def _article(self, article_id: str) -> dict[str, Any]:
        result = self.articles.obtener(str(article_id or ""))
        article = dict(result.get("articulo") or {}) if result.get("ok") else {}
        if not article:
            raise ErrorConfirmacionRelacionIngrediente("article_not_found", "El artículo canónico no existe.")
        return article

    @staticmethod
    def _fingerprint(recipe: Any) -> str:
        return hashlib.sha256(json.dumps(asdict(recipe), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    @staticmethod
    def _token(recipe_id: str, ingredient_index: int, article_id: str, fingerprint: str) -> str:
        value = json.dumps({"recipe_id": recipe_id, "ingredient_index": ingredient_index, "article_id": article_id, "version": fingerprint}, sort_keys=True)
        return hashlib.sha256(value.encode("utf-8")).hexdigest()


__all__ = ["ConfirmacionRelacionIngredienteService", "ErrorConfirmacionRelacionIngrediente"]