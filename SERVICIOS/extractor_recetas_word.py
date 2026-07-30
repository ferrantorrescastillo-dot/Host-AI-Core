from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService
from SERVICIOS.importador_inteligente_recetas_m131 import clasificar_prefijo_articulo
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


class WordRecipeExtractor:
    """Extrae borradores revisables desde bloques DOCX sin persistirlos."""

    SECTION_NAMES = {
        "ingredientes", "elaboracion", "procedimiento", "preparacion", "metodo",
        "rendimiento", "raciones", "presentacion", "conservacion", "alergenos",
        "observaciones", "notas", "escandallo",
    }
    UNIT_MAP = {
        "kg": "kg", "kilo": "kg", "kilos": "kg",
        "g": "g", "gr": "g", "gramo": "g", "gramos": "g",
        "l": "l", "litro": "l", "litros": "l",
        "ml": "ml", "cl": "cl",
        "u": "ud", "ud": "ud", "uds": "ud", "unidad": "ud", "unidades": "ud",
        "pieza": "ud", "piezas": "ud",
    }
    INGREDIENT_RE = re.compile(
        r"^[\s\-•·]*(?P<quantity>\d+(?:[.,]\d+)?(?:\s+\d+(?:[.,]\d+)?)?)\s*"
        r"(?P<unit>kg|kilos?|g|gr|gramos?|l|litros?|ml|cl|u|ud|uds|unidades?|piezas?)"
        r"\s+(?:de\s+)?(?P<name>.+)$",
        re.IGNORECASE,
    )

    def __init__(self, base_dir: Path) -> None:
        self.catalog = RepositorioProductosMaestro601(base_dir)
        self.library = BibliotecaCulinariaReadService(base_dir)

    @staticmethod
    def _norm(value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or "").lower())
        return " ".join(
            "".join(char for char in text if not unicodedata.combining(char)).split()
        ).strip(" .,:;-_")

    def extract(self, blocks: list[dict[str, Any]]) -> dict[str, Any]:
        groups = self._recipe_groups(blocks) if self._has_recipe_evidence(blocks) else []
        recipes = [self._parse_recipe(index, title, content) for index, (title, content) in enumerate(groups, 1)]
        recipes = [recipe for recipe in recipes if recipe["nombre"]]
        ingredients = [
            ingredient
            for recipe in recipes
            for ingredient in recipe["ingredientes_estructurados"]
        ]
        return {
            "recetas": recipes,
            "ingredientes": ingredients,
            "productos_existentes": [
                ingredient["nombre_normalizado"]
                for ingredient in ingredients
                if ingredient["estado_relacion"] == "relacionado"
            ],
            "productos_nuevos": [
                {"nombre": ingredient["nombre_original"], "receta": ingredient["receta"]}
                for ingredient in ingredients
                if ingredient["estado_relacion"] == "sin_relacionar"
            ],
            "incidencias": self._incidents(recipes, ingredients),
        }

    def _has_recipe_evidence(self, blocks: list[dict[str, Any]]) -> bool:
        for block in blocks:
            text = str(block.get("texto") or "").strip()
            normalized = self._norm(text)
            if normalized.startswith("receta:") or normalized in {
                "ingredientes", "elaboracion", "procedimiento", "preparacion", "rendimiento",
            }:
                return True
            if self.INGREDIENT_RE.match(text):
                return True
            if block.get("tipo") == "table":
                headers = {
                    self._norm(cell)
                    for row in list(block.get("filas") or [])[:1]
                    for cell in list(row)
                }
                if headers & {"ingrediente", "producto", "articulo"}:
                    return True
        return False

    def _recipe_groups(
        self,
        blocks: list[dict[str, Any]],
    ) -> list[tuple[str, list[dict[str, Any]]]]:
        usable = [block for block in blocks if str(block.get("texto") or "").strip()]
        heading_indexes = [
            index
            for index, block in enumerate(usable)
            if block.get("tipo") == "heading"
            and self._norm(block.get("texto")) not in self.SECTION_NAMES
        ]
        if heading_indexes:
            groups = []
            for position, start in enumerate(heading_indexes):
                end = heading_indexes[position + 1] if position + 1 < len(heading_indexes) else len(usable)
                groups.append((str(usable[start]["texto"]).strip(), usable[start + 1:end]))
            return groups

        explicit = [
            index
            for index, block in enumerate(usable)
            if self._norm(block.get("texto")).startswith("receta:")
        ]
        if explicit:
            groups = []
            for position, start in enumerate(explicit):
                end = explicit[position + 1] if position + 1 < len(explicit) else len(usable)
                title = str(usable[start]["texto"]).split(":", 1)[1].strip()
                groups.append((title, usable[start + 1:end]))
            return groups

        if not usable:
            return []
        title = str(usable[0].get("texto") or "").strip()
        return [(title, usable[1:])]

    def _parse_recipe(
        self,
        index: int,
        title: str,
        blocks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        ingredients: list[dict[str, Any]] = []
        procedure: list[str] = []
        warnings: list[str] = []
        rendement: float | None = None
        source_blocks = [str(block.get("referencia_origen") or f"bloque:{block.get('orden')}") for block in blocks]

        for block in blocks:
            if block.get("tipo") == "table":
                ingredients.extend(self._table_ingredients(block, title))
                continue
            text = str(block.get("texto") or "").strip()
            normalized = self._norm(text)
            if not text or normalized in self.SECTION_NAMES or normalized.isdigit():
                continue
            rendement_match = re.search(
                r"(?:rendimiento|raciones?|para)\s*[:=]?\s*(\d+(?:[.,]\d+)?)",
                normalized,
            )
            if rendement_match:
                rendement = float(rendement_match.group(1).replace(",", "."))
                continue
            ingredient = self._ingredient(text, block, title)
            if ingredient:
                ingredients.append(ingredient)
                if " " in ingredient["cantidad_texto"].strip():
                    warnings.append(
                        f"Cantidad ambigua pendiente de revisión: {ingredient['cantidad_texto']}."
                    )
            else:
                procedure.append(text)

        duplicate = self._recipe_match(title)
        return {
            "id_origen": f"REC-WORD-{index:03d}",
            "nombre": title,
            "numero_raciones": rendement,
            "rendimiento": rendement,
            "ingredientes": [item["nombre_original"] for item in ingredients],
            "cantidades": [
                " ".join(filter(None, (item["cantidad_texto"], item["unidad"])))
                for item in ingredients
            ],
            "ingredientes_estructurados": ingredients,
            "elaboracion": "\n".join(procedure).strip(),
            "pasos": procedure,
            "bloques_origen": source_blocks,
            "advertencias": warnings,
            "coincidencia_biblioteca": duplicate,
        }

    def _ingredient(
        self,
        text: str,
        block: dict[str, Any],
        recipe_name: str,
    ) -> dict[str, Any] | None:
        match = self.INGREDIENT_RE.match(text)
        if not match:
            return None
        quantity_text = match.group("quantity")
        quantity = None
        if " " not in quantity_text and re.fullmatch(r"\d+(?:[.,]\d+)?", quantity_text):
            try:
                quantity = float(quantity_text.replace(",", "."))
            except ValueError:
                quantity = None
        unit = self.UNIT_MAP.get(self._norm(match.group("unit")), self._norm(match.group("unit")))
        name = match.group("name").strip(" .,:;-")
        return self._linked_ingredient(
            name=name,
            quantity=quantity,
            quantity_text=quantity_text,
            unit=unit,
            observations="",
            source=str(block.get("referencia_origen") or f"bloque:{block.get('orden')}"),
            recipe_name=recipe_name,
        )

    def _table_ingredients(
        self,
        block: dict[str, Any],
        recipe_name: str,
    ) -> list[dict[str, Any]]:
        rows = [list(row) for row in block.get("filas") or []]
        if not rows:
            return []
        headers = [self._norm(value) for value in rows[0]]
        name_index = next((i for i, value in enumerate(headers) if value in {"ingrediente", "producto", "articulo"}), None)
        quantity_index = next((i for i, value in enumerate(headers) if value in {"cantidad", "peso"}), None)
        unit_index = next((i for i, value in enumerate(headers) if value in {"unidad", "ud", "um"}), None)
        start = 1 if name_index is not None else 0
        output: list[dict[str, Any]] = []
        for row_index, row in enumerate(rows[start:], start):
            if name_index is not None and name_index < len(row):
                name = str(row[name_index]).strip()
                quantity_text = str(row[quantity_index]).strip() if quantity_index is not None and quantity_index < len(row) else ""
                unit = self.UNIT_MAP.get(
                    self._norm(row[unit_index]) if unit_index is not None and unit_index < len(row) else "",
                    self._norm(row[unit_index]) if unit_index is not None and unit_index < len(row) else "",
                )
                try:
                    quantity = float(quantity_text.replace(",", ".")) if quantity_text else None
                except ValueError:
                    quantity = None
                if name:
                    output.append(self._linked_ingredient(
                        name=name,
                        quantity=quantity,
                        quantity_text=quantity_text,
                        unit=unit,
                        observations="",
                        source=f"{block.get('referencia_origen')}:fila:{row_index}",
                        recipe_name=recipe_name,
                    ))
            else:
                combined = " ".join(str(value) for value in row if str(value).strip())
                ingredient = self._ingredient(combined, block, recipe_name)
                if ingredient:
                    output.append(ingredient)
        return output

    def _linked_ingredient(
        self,
        *,
        name: str,
        quantity: float | None,
        quantity_text: str,
        unit: str,
        observations: str,
        source: str,
        recipe_name: str,
    ) -> dict[str, Any]:
        normalized = self._norm(name)
        candidates = [
            item
            for item in self.catalog.buscar_productos({"nombre": name})
            if clasificar_prefijo_articulo(item) != "APERITIVO"
        ]
        exact = [item for item in candidates if self._norm(item.get("nombre")) == normalized]
        linked = exact[0] if len(exact) == 1 else None
        status = (
            "relacionado"
            if linked
            else ("coincidencia_dudosa" if candidates else "sin_relacionar")
        )
        return {
            "nombre_original": name,
            "nombre_normalizado": normalized,
            "cantidad": quantity,
            "cantidad_texto": quantity_text,
            "unidad": unit or None,
            "observaciones": observations or None,
            "bloque_origen": source,
            "confianza": 0.98 if linked else (0.6 if candidates else 0.45),
            "articulo_id": str(linked.get("codigo") or linked.get("id")) if linked else None,
            "estado_relacion": status,
            "candidatos": [
                {"id": str(item.get("codigo") or item.get("id") or ""), "nombre": item.get("nombre")}
                for item in candidates[:5]
            ],
            "receta": recipe_name,
        }

    def _recipe_match(self, name: str) -> dict[str, Any]:
        result = self.library.listar({"q": name, "page": 1, "page_size": 100})
        items = list((result.get("elaboraciones") or {}).get("items") or [])
        normalized = self._norm(name)
        exact = [item for item in items if self._norm(item.get("nombre")) == normalized]
        if exact:
            return {"estado": "coincidencia_exacta", "candidatos": exact[:5]}
        if items:
            return {"estado": "posible_duplicado", "candidatos": items[:5]}
        return {"estado": "nueva_entidad", "candidatos": []}

    @staticmethod
    def _incidents(
        recipes: list[dict[str, Any]],
        ingredients: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        incidents = []
        for recipe in recipes:
            if not recipe["ingredientes"]:
                incidents.append({"tipo": "RECETA_SIN_INGREDIENTES", "detalle": recipe["nombre"]})
            if not recipe["elaboracion"]:
                incidents.append({"tipo": "RECETA_SIN_PROCEDIMIENTO", "detalle": recipe["nombre"]})
        for ingredient in ingredients:
            if ingredient["estado_relacion"] != "relacionado":
                incidents.append({
                    "tipo": ingredient["estado_relacion"].upper(),
                    "detalle": ingredient["nombre_original"],
                })
        return incidents


__all__ = ["WordRecipeExtractor"]
