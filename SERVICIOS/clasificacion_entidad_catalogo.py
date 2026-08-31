from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any


ARTICULO_COMPRADO = "ARTICULO_COMPRADO"
ELABORACION_INTERNA = "ELABORACION_INTERNA"
SUBELABORACION = "SUBELABORACION"
PRODUCTO_VENDIBLE = "PRODUCTO_VENDIBLE"
TIPOS_ENTIDAD = frozenset({
    ARTICULO_COMPRADO,
    ELABORACION_INTERNA,
    SUBELABORACION,
    PRODUCTO_VENDIBLE,
})
TIPOS_COSTE_DERIVADO = frozenset({ELABORACION_INTERNA, SUBELABORACION})


def normalizar_tipo(value: Any) -> str:
    candidate = str(value or "").strip().upper()
    return candidate if candidate in TIPOS_ENTIDAD else ARTICULO_COMPRADO


def relacion_elaboracion(article: dict[str, Any]) -> str | None:
    value = str(article.get("elaboracion_id") or "").strip()
    return value or None


def requiere_precio_compra(article: dict[str, Any]) -> bool:
    """Solo excluye entidades derivadas cuando la relación es explícita."""
    kind = normalizar_tipo(article.get("tipo_entidad"))
    if kind in TIPOS_COSTE_DERIVADO:
        return relacion_elaboracion(article) is None
    if kind == PRODUCTO_VENDIBLE and relacion_elaboracion(article):
        return False
    return True


def origen_coste(article: dict[str, Any]) -> str:
    return (
        "COSTE_DERIVADO_ELABORACION"
        if not requiere_precio_compra(article)
        else "COSTE_COMPRA"
    )


class AuditorClasificacionLegada:
    """Detecta candidatos de migración sin alterar ni vincular registros."""

    def __init__(self, base_dir: Path | str) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.db_dir = self.base_dir / "DATOS" / "db"

    def candidatos(self) -> dict[str, Any]:
        articles = self._read_list("articulos.json")
        recipes = self._recipes()
        by_name: dict[str, list[dict[str, str]]] = {}
        for recipe in recipes:
            name = str(recipe.get("nombre") or "").strip()
            recipe_id = str(recipe.get("receta_id") or recipe.get("codigo") or recipe.get("id") or "").strip()
            if name and recipe_id:
                by_name.setdefault(self._norm(name), []).append({"elaboracion_id": recipe_id, "nombre": name})

        candidates = []
        for article in articles:
            if relacion_elaboracion(article) or normalizar_tipo(article.get("tipo_entidad")) != ARTICULO_COMPRADO:
                continue
            matches = by_name.get(self._norm(article.get("nombre")), [])
            observations = self._norm(article.get("observaciones"))
            signals = []
            if matches:
                signals.append("MISMO_NOMBRE_ELABORACION")
            if "elaboracion" in observations:
                signals.append("OBSERVACION_LEGADA_ELABORACION")
            if str(article.get("origen") or "").lower() == "excel":
                signals.append("ORIGEN_EXCEL")
            if article.get("precio") in (None, ""):
                signals.append("SIN_PRECIO")
            if not matches or len(signals) < 2:
                continue
            candidates.append({
                "article_id": str(article.get("id") or article.get("codigo") or ""),
                "articulo": str(article.get("nombre") or ""),
                "registro_actual": {key: article.get(key) for key in ("tipo_entidad", "precio", "proveedor", "origen", "observaciones", "familia")},
                "coincidencias": matches,
                "senales": signals,
                "estado": "REQUIERE_REVISION",
                "acciones_permitidas": [
                    "VINCULAR_COMO_ELABORACION",
                    "MANTENER_COMO_ARTICULO_COMPRADO",
                    "REVISAR",
                ],
            })
        return {
            "ok": True,
            "candidatos": candidates,
            "total": len(candidates),
            "requiere_preview_confirm": True,
            "datos_reales_modificados": False,
        }

    def _recipes(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for name in ("biblioteca_recetas_601.json", "escandallos_canonicos.json", "escandallos.json"):
            value = self._read(name)
            rows = value if isinstance(value, list) else list((value or {}).get("escandallos") or (value or {}).get("recetas") or [])
            for row in rows:
                if not isinstance(row, dict):
                    continue
                recipe = row.get("receta") if isinstance(row.get("receta"), dict) else row
                result.append(dict(recipe))
        return result

    def _read_list(self, name: str) -> list[dict[str, Any]]:
        value = self._read(name)
        return [dict(row) for row in value] if isinstance(value, list) else []

    def _read(self, name: str) -> Any:
        path = self.db_dir / name
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []

    @staticmethod
    def _norm(value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or ""))
        return "".join(char for char in text if not unicodedata.combining(char)).strip().casefold()


class ClasificadorImportacionEntidades:
    """Clasificación determinista para la fase de análisis; nunca persiste."""

    def analizar(self, recipes: list[dict[str, Any]]) -> dict[str, Any]:
        recipe_names = {self._norm(row.get("nombre") or row.get("receta")): row for row in recipes if self._norm(row.get("nombre") or row.get("receta"))}
        used_as_component: set[str] = set(); purchased: dict[str, dict[str, Any]] = {}
        relations = []
        for recipe in recipes:
            recipe_name = str(recipe.get("nombre") or recipe.get("receta") or "").strip()
            ingredients = list(recipe.get("ingredientes") or recipe.get("lineas") or [])
            for ingredient in ingredients:
                if not isinstance(ingredient, dict): continue
                name = str(ingredient.get("nombre") or ingredient.get("ingrediente") or ingredient.get("producto") or "").strip()
                key = self._norm(name)
                if not key: continue
                if key in recipe_names:
                    used_as_component.add(key)
                    relations.append({"receta": recipe_name, "componente": name, "tipo_componente_propuesto": "ELABORACION", "estado": "REQUIERE_REVISION"})
                else:
                    purchased.setdefault(key, {"nombre": name, "tipo_entidad_propuesto": ARTICULO_COMPRADO, "estado": "PROPUESTA"})
        elaborations = []
        for key, recipe in recipe_names.items():
            kind = SUBELABORACION if key in used_as_component else ELABORACION_INTERNA
            elaborations.append({"nombre": recipe.get("nombre") or recipe.get("receta"), "tipo_entidad_propuesto": kind, "estado": "REQUIERE_REVISION"})
        return {
            "articulos_comprados": sorted(purchased.values(), key=lambda row: self._norm(row["nombre"])),
            "elaboraciones": elaborations,
            "subelaboraciones": [row for row in elaborations if row["tipo_entidad_propuesto"] == SUBELABORACION],
            "productos_vendibles_candidatos": [{"nombre": row["nombre"], "tipo_entidad_propuesto": PRODUCTO_VENDIBLE, "estado": "REQUIERE_REVISION"} for row in elaborations if row["tipo_entidad_propuesto"] == ELABORACION_INTERNA],
            "relaciones": relations,
            "resumen": {"recetas_detectadas": len(recipes), "articulos_comprados_unicos": len(purchased), "elaboraciones": len(elaborations), "subelaboraciones": len(used_as_component), "productos_vendibles_candidatos": sum(1 for row in elaborations if row["tipo_entidad_propuesto"] == ELABORACION_INTERNA), "relaciones_ambiguas": len(relations)},
            "requiere_revision": True, "datos_reales_modificados": False,
        }

    @staticmethod
    def _norm(value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or ""))
        return "".join(char for char in text if not unicodedata.combining(char)).strip().casefold()


__all__ = [
    "ARTICULO_COMPRADO", "ELABORACION_INTERNA", "SUBELABORACION",
    "PRODUCTO_VENDIBLE", "TIPOS_ENTIDAD", "normalizar_tipo",
    "relacion_elaboracion", "requiere_precio_compra", "origen_coste",
    "AuditorClasificacionLegada", "ClasificadorImportacionEntidades",
]
