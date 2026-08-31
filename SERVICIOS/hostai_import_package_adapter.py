from __future__ import annotations

import base64
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from MODELOS.hostai_import_package import (
    HOST_AI_IMPORT_PACKAGE_SCHEMA,
    HOST_AI_IMPORT_PACKAGE_VERSION,
    HostAIImportPackage,
    HostAIImportPackageError,
)


class PreparedImportPackageAdapter:
    """Valida una interpretación externa y la proyecta al pipeline existente.

    El adaptador no resuelve identidades, no escribe y no acepta autoridad operativa.
    """

    ROOT_FIELDS = {
        "schema", "version", "metadata", "recipes", "articles", "suppliers", "menus",
        "relations", "ambiguities", "variant_groups", "entities",
    }
    ENTITY_FIELDS = {"recipes", "articles", "suppliers", "menus"}
    UNSAFE_FIELDS = {
        "stock", "stocks", "lots", "lotes", "movements", "movimientos", "receipts",
        "recepciones", "purchases", "compras", "orders", "pedidos", "permissions",
        "permisos", "canonical_id", "canonical_recipe_id", "recipe_id", "receta_id",
        "article_id", "articulo_id", "supplier_id", "proveedor_id", "menu_id",
        "create_lot", "crear_lote", "create_movement", "crear_movimiento", "invoices",
        "facturas", "real_price", "precio_real",
    }

    @classmethod
    def can_handle(cls, payload: dict[str, Any]) -> bool:
        if isinstance(payload.get("hostai_import_package"), dict):
            return True
        try:
            raw, _ = cls._package_input(payload)
            return isinstance(raw, dict) and raw.get("schema") == HOST_AI_IMPORT_PACKAGE_SCHEMA
        except (HostAIImportPackageError, json.JSONDecodeError, UnicodeDecodeError):
            return False

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw, source = self._package_input(payload)
        package = self.validate(raw)
        recipes = self._recipes(package, source)
        articles = [self._article(item, source) for item in package.articles]
        suppliers = [self._supplier(item, source) for item in package.suppliers]
        menus = [self._menu(item, source) for item in package.menus]
        relations = [self._relation(item, source) for item in package.relations]
        ambiguities = [self._ambiguity(item, source) for item in package.ambiguities]
        ingredients = sum(len(item.get("ingredientes_estructurados") or []) for item in recipes)
        return {
            "archivos": [{
                "nombre": source, "tipo": "json", "tamano": len(json.dumps(raw, ensure_ascii=False).encode("utf-8")),
                "estado": "ANALIZADO", "hojas": 1, "filas": len(recipes) + len(articles) + len(suppliers),
            }],
            "hojas": [{
                "archivo": source, "nombre": "HostAIImportPackage", "region": "PACKAGE-0.1",
                "tipo_propuesto": "PAQUETE_PREPARADO", "filas": len(recipes) + len(articles),
                "mapping": [], "confianza": 1.0, "motivo": "Contrato versionado validado.",
            }],
            "resumen": {
                "archivos_analizados": 1, "hojas_analizadas": 1,
                "filas_analizadas": len(recipes) + len(articles) + len(suppliers),
                "posibles_articulos": len(articles), "posibles_recetas": len(recipes),
                "posibles_subelaboraciones": sum(r.get("tipo_entidad_propuesto") == "SUBELABORACION" for r in recipes),
                "posibles_productos_vendibles": len(menus), "proveedores": len(suppliers),
                "relaciones_detectadas": len(relations), "duplicados_posibles": 0,
                "ambiguedades": len(ambiguities), "decisiones_usuario": len(ambiguities),
                "warnings_tecnicos": len(package.warnings),
                "articulos_sin_coste": sum(item.get("precio_compra") in {None, ""} for item in articles),
                "ingredientes_detectados": ingredients,
            },
            "mapping": [], "recetas": recipes, "articulos": articles,
            "proveedores": suppliers, "menus": menus, "relaciones": relations,
            "duplicados": [],
            "dudas": {"clasificacion": ambiguities, "precio": [], "relaciones": ambiguities},
            "regiones_ambiguas": [], "decisiones_usuario": ambiguities,
            "warnings_tecnicos": list(package.warnings),
            "perfiles_importacion": [],
            "resultado_hibrido": {
                "origen": "HOSTAI_IMPORT_PACKAGE", "version": package.version,
                "recetas_consolidadas": len(recipes), "variantes": sum(r.get("posible_variante") for r in recipes),
                "warnings_tecnicos": len(package.warnings), "decisiones_usuario": len(ambiguities),
            },
            "coste_ia": {"usada": False, "llamadas": 0, "ambiguedades_enviadas": 0},
            "package_metadata": deepcopy(package.metadata),
        }

    @classmethod
    def validate(cls, raw: Any) -> HostAIImportPackage:
        if not isinstance(raw, dict):
            raise HostAIImportPackageError("El paquete debe ser un objeto JSON.")
        if raw.get("schema") != HOST_AI_IMPORT_PACKAGE_SCHEMA:
            raise HostAIImportPackageError("Schema HostAIImportPackage no reconocido.")
        if str(raw.get("version") or "") != HOST_AI_IMPORT_PACKAGE_VERSION:
            raise HostAIImportPackageError("Versión HostAIImportPackage no soportada; se admite 0.1.")
        unsafe = cls._unsafe_paths(raw)
        if unsafe:
            raise HostAIImportPackageError(
                "El paquete contiene campos con autoridad operativa no admitida: " + ", ".join(unsafe[:10])
            )
        warnings = [f"Campo desconocido ignorado: {key}" for key in raw if key not in cls.ROOT_FIELDS]
        entities = raw.get("entities") or {}
        if not isinstance(entities, dict):
            raise HostAIImportPackageError("entities debe ser un objeto.")
        warnings.extend(f"Colección desconocida ignorada: entities.{key}" for key in entities if key not in cls.ENTITY_FIELDS)
        metadata = raw.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise HostAIImportPackageError("metadata debe ser un objeto.")

        def collection(name: str) -> list[dict[str, Any]]:
            value = raw.get(name, entities.get(name, []))
            if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
                raise HostAIImportPackageError(f"{name} debe ser una lista de objetos.")
            return deepcopy(value)

        recipes = collection("recipes")
        articles = collection("articles")
        suppliers = collection("suppliers")
        menus = collection("menus")
        relations = collection("relations")
        ambiguities = collection("ambiguities")
        variant_groups = collection("variant_groups")
        for label, items in (("recipes", recipes), ("articles", articles), ("suppliers", suppliers), ("menus", menus)):
            for index, item in enumerate(items):
                if not str(item.get("name") or "").strip():
                    raise HostAIImportPackageError(f"{label}[{index}] requiere name.")
        return HostAIImportPackage(
            schema=HOST_AI_IMPORT_PACKAGE_SCHEMA, version=HOST_AI_IMPORT_PACKAGE_VERSION,
            metadata=deepcopy(metadata), recipes=recipes, articles=articles, suppliers=suppliers,
            menus=menus, relations=relations, ambiguities=ambiguities,
            variant_groups=variant_groups, warnings=tuple(warnings),
        )

    @classmethod
    def _unsafe_paths(cls, value: Any, path: str = "$") -> list[str]:
        found: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if str(key).casefold() in cls.UNSAFE_FIELDS:
                    found.append(child_path)
                else:
                    found.extend(cls._unsafe_paths(child, child_path))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                found.extend(cls._unsafe_paths(child, f"{path}[{index}]"))
        return found

    @classmethod
    def _package_input(cls, payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
        direct = payload.get("hostai_import_package")
        if isinstance(direct, dict):
            return deepcopy(direct), "hostai-import-package.json"
        inputs = list(payload.get("archivos") or [])
        if len(inputs) != 1:
            raise HostAIImportPackageError("El paquete preparado debe enviarse como un único JSON.")
        item = inputs[0]
        name = Path(str(item.get("nombre") or "hostai-import-package.json")).name
        text = str(item.get("texto") or "")
        if not text and item.get("contenido_base64"):
            try:
                text = base64.b64decode(str(item["contenido_base64"]), validate=True).decode("utf-8")
            except (ValueError, UnicodeDecodeError) as exc:
                raise HostAIImportPackageError("El JSON preparado no se puede decodificar.") from exc
        return json.loads(text), name

    @staticmethod
    def _provenance(item: dict[str, Any], source: str) -> dict[str, Any]:
        provenance = deepcopy(item.get("provenance") or {})
        return {"archivo": source, "origen_detector": "HOSTAI_IMPORT_PACKAGE", **provenance}

    def _recipes(self, package: HostAIImportPackage, source: str) -> list[dict[str, Any]]:
        recipes = [self._recipe(item, source) for item in package.recipes]
        for group_index, group in enumerate(package.variant_groups, 1):
            versions = group.get("versions") or group.get("variantes") or []
            if not isinstance(versions, list):
                raise HostAIImportPackageError(f"variant_groups[{group_index - 1}].versions debe ser una lista.")
            group_name = str(group.get("name") or group.get("nombre") or f"Variante {group_index}")
            for version in versions:
                if not isinstance(version, dict):
                    raise HostAIImportPackageError("Cada versión de variante debe ser un objeto.")
                recipes.append(self._recipe({"name": group_name, **version, "possible_variant": True}, source))
        return recipes

    def _recipe(self, item: dict[str, Any], source: str) -> dict[str, Any]:
        name = str(item.get("name") or item.get("nombre") or "").strip()
        ingredients = []
        for ingredient in item.get("ingredients") or item.get("ingredientes") or []:
            if not isinstance(ingredient, dict):
                raise HostAIImportPackageError(f"Ingrediente inválido en {name}.")
            ingredient_name = str(ingredient.get("name") or ingredient.get("nombre") or "").strip()
            ingredient_quantity = ingredient.get("quantity") if "quantity" in ingredient else ingredient.get("cantidad")
            if ingredient_name.isdecimal() and ingredient_quantity in {None, ""}:
                continue
            ingredients.append({
                "nombre_original": ingredient_name,
                "cantidad": ingredient.get("quantity") or ingredient.get("cantidad"),
                "cantidad_texto": str(ingredient.get("quantity_text") or ingredient.get("cantidad_texto") or ingredient.get("quantity") or ingredient.get("cantidad") or ""),
                "unidad": ingredient.get("unit") or ingredient.get("unidad"),
                "trazabilidad": self._provenance(ingredient, source),
                "confidence": ingredient.get("confidence"),
                "interpretation": ingredient.get("interpretation"),
                "observed": ingredient.get("observed"),
            })
        occurrences = item.get("occurrences") or [item.get("provenance") or {}]
        return {
            "id_origen": item.get("source_id") or item.get("id_origen"), "nombre": name,
            "ingredientes_estructurados": ingredients,
            "rendimiento": item.get("yield") if "yield" in item else item.get("rendimiento"),
            "numero_raciones": item.get("servings") or item.get("numero_raciones"),
            "unidad_rendimiento": item.get("yield_unit") or item.get("unidad_rendimiento"),
            "pasos": list(item.get("procedure") or item.get("pasos") or []),
            "tipo": item.get("type") or item.get("tipo"),
            "tipo_entidad_propuesto": item.get("entity_type") or item.get("tipo_entidad_propuesto") or "ELABORACION_INTERNA",
            "bloques_origen": [self._provenance(x if isinstance(x, dict) else {"referencia": x}, source) for x in occurrences],
            "origen_detector": "HOSTAI_IMPORT_PACKAGE", "origenes_detector": ["HOSTAI_IMPORT_PACKAGE"],
            "confidence": item.get("confidence"), "observed": item.get("observed"),
            "interpretation": item.get("interpretation"),
            "aliases": list(item.get("aliases") or []),
            "contexto": deepcopy(item.get("context") or item.get("contexto")),
            "costes_documento": deepcopy(item.get("document_costs") or item.get("costes_documento") or []),
            "posible_variante": bool(item.get("possible_variant") or item.get("posible_variante")),
        }

    def _article(self, item: dict[str, Any], source: str) -> dict[str, Any]:
        raw_price = item.get("document_price") if "document_price" in item else (
            item.get("reference_price") if "reference_price" in item else item.get("precio_referencia")
        )
        price_record = deepcopy(raw_price) if isinstance(raw_price, dict) else (
            {"value": raw_price} if raw_price is not None else None
        )
        price = price_record.get("value") if price_record else None
        if price_record is not None:
            price_record.setdefault("type", "PRECIO_REFERENCIA_IMPORTADO")
            price_record.setdefault("provenance", self._provenance(item, source))
        return {
            "nombre": item.get("name") or item.get("nombre"), "codigo": item.get("source_code") or item.get("codigo_origen"),
            "familia": item.get("family") or item.get("familia"), "unidad_base": item.get("unit") or item.get("unidad_base"),
            "proveedor": item.get("supplier") or item.get("proveedor"), "formato": item.get("format") or item.get("formato"),
            "precio_compra": price, "precio_referencia_importado": price_record,
            "precio_tipo": "REFERENCIA_IMPORTADA_NO_APLICABLE" if price is not None else None,
            "origen": self._provenance(item, source), "confidence": item.get("confidence"),
            "tipo_semantico": (
                item.get("entity_type") or item.get("kind_candidate") or item.get("semantic_type")
                or item.get("classification") or (item.get("interpretation") or {}).get("classification")
                or (item.get("observed") or {}).get("clasificacion_chatgpt")
            ),
            "evidencia_tipo": deepcopy({
                "interpretation": item.get("interpretation"), "observed": item.get("observed"),
                "context": item.get("context"), "confidence": item.get("confidence"),
            }),
        }

    def _supplier(self, item: dict[str, Any], source: str) -> dict[str, Any]:
        return {"nombre": item.get("name") or item.get("nombre"), "origen": self._provenance(item, source)}

    def _menu(self, item: dict[str, Any], source: str) -> dict[str, Any]:
        kind = str(item.get("kind") or item.get("tipo") or "MENU").upper()
        if kind not in {"MENU", "CONTEXT", "CONTENEDOR", "PRODUCTO_VENDIBLE"}:
            kind = "CONTENEDOR"
        return {"nombre": item.get("name") or item.get("nombre"), "tipo": kind, "componentes": deepcopy(item.get("items") or item.get("componentes") or []), "origen": self._provenance(item, source)}

    def _relation(self, item: dict[str, Any], source: str) -> dict[str, Any]:
        return {"elaboracion": item.get("from") or item.get("elaboracion"), "depende_de": item.get("to") or item.get("depende_de"), "tipo_propuesto": item.get("type") or item.get("tipo_propuesto") or "SUBELABORACION", "origen": self._provenance(item, source)}

    def _ambiguity(self, item: dict[str, Any], source: str) -> dict[str, Any]:
        return {"tipo": item.get("type") or item.get("tipo") or "REQUIERE_REVISION", "nombre": item.get("name") or item.get("nombre") or "Decisión pendiente", "motivo": item.get("reason") or item.get("motivo") or "La interpretación externa requiere validación humana.", "origen": self._provenance(item, source)}
