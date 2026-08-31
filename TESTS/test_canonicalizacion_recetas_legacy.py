from __future__ import annotations

import json
from pathlib import Path

from CORE.entidades.escandallo import Escandallo
from CORE.entidades.ingrediente import Ingrediente
from CORE.entidades.receta import Receta
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.canonicalizacion_recetas_legacy_service import (
    LEGACY_SOURCE_TYPE,
    LEGACY_WITHOUT_CANONICAL,
    LegacyRecipeCanonicalizationService,
)
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


def context() -> AuthorizedExecutionContext:
    return AuthorizedExecutionContext(
        "REQ-LEGACY", "chef", "restaurant", ("chef",),
        frozenset({"recetas:preview", "recetas:write"}),
    )


def seed_article(base: Path, code: str, name: str) -> None:
    RepositorioProductosMaestro601(base).crear_producto({
        "codigo": code, "nombre": name, "unidad_base": "kg",
    })


def ingredient(code: str, name: str, *, dependency: str = "") -> Ingrediente:
    return Ingrediente(
        codigo=code, nombre=name, cantidad=1, unidad="kg", articulo_id=code,
        metadata={"tipo": "ELABORACION" if dependency else "ARTICULO",
                  "referencia_elaboracion": dependency or None},
    )


def legacy(code: str, name: str, ingredients: list[Ingrediente]) -> Escandallo:
    return Escandallo(Receta(code, name, 10, "u", ingredients), coste_total=12.5)


def stock_snapshot(base: Path) -> dict[str, bytes | None]:
    names = (
        "stock_lotes.json", "stock_movimientos.json", "compras_recepciones.json",
    )
    return {
        name: (base / "DATOS" / "db" / name).read_bytes()
        if (base / "DATOS" / "db" / name).exists() else None
        for name in names
    }


def test_preview_confirm_canonicalizes_legacy_preserving_provenance_and_no_stock(tmp_path: Path):
    seed_article(tmp_path, "ART-CORVINA", "Corvina")
    RepositorioEscandallos(tmp_path / "DATOS/db/escandallos_canonicos.json").guardar_todos([
        legacy("REC-LEG-CEVICHE", "Ceviche de corvina", [ingredient("ART-CORVINA", "Corvina")]),
    ])
    db = tmp_path / "DATOS" / "db"; db.mkdir(parents=True, exist_ok=True)
    for name in ("stock_lotes.json", "stock_movimientos.json", "compras_recepciones.json"):
        (db / name).write_text(json.dumps([{"fixture": name}]), encoding="utf-8")
    before_stock = stock_snapshot(tmp_path)
    service = LegacyRecipeCanonicalizationService(tmp_path)

    analysis = service.analyze()
    preview = service.preview(legacy_ids=["REC-LEG-CEVICHE"], context=context())

    assert analysis["casos"][0]["estado"] == LEGACY_WITHOUT_CANONICAL
    assert preview["datos_reales_modificados"] is False
    assert RepositorioBibliotecaRecetas601(tmp_path).listar() == []
    assert preview["resumen_impacto"] == {
        "recetas_601": 1, "stock": 0, "lotes": 0,
        "movimientos_stock": 0, "recepciones": 0, "compras": 0,
    }

    confirmed = service.confirm(preview_token=preview["preview_token"], context=context())
    stored = RepositorioBibliotecaRecetas601(tmp_path).listar()[0]
    history = stored["historial_procedencia"]
    assert confirmed["estado"] == "CONFIRMADO"
    assert stored["estado"] == "PENDIENTE_DE_COMPLETAR"
    assert stored["ingredientes_estructurados"][0]["article_id"] == "ART-CORVINA"
    assert any(item["tipo"] == LEGACY_SOURCE_TYPE and item["legacy_source_id"] == "REC-LEG-CEVICHE" and item["canonical_recipe_id"] == stored["id"] for item in history)
    assert stored["precio"] == ""
    assert stock_snapshot(tmp_path) == before_stock


def test_canonicalization_is_idempotent_across_token_and_new_service(tmp_path: Path):
    seed_article(tmp_path, "ART-A", "Ingrediente A")
    RepositorioEscandallos(tmp_path / "DATOS/db/escandallos_canonicos.json").guardar_todos([
        legacy("REC-LEG-A", "Receta A", [ingredient("ART-A", "Ingrediente A")]),
    ])
    service = LegacyRecipeCanonicalizationService(tmp_path)
    preview = service.preview(legacy_ids=["REC-LEG-A"], context=context())
    first = service.confirm(preview_token=preview["preview_token"], context=context())
    replay = service.confirm(preview_token=preview["preview_token"], context=context())
    fresh = LegacyRecipeCanonicalizationService(tmp_path)

    assert first["idempotente"] is False
    assert replay["idempotente"] is True
    assert fresh.analyze()["casos"][0]["estado"] == "REUTILIZAR_EXISTENTE_CANONICA"
    assert len(RepositorioBibliotecaRecetas601(tmp_path).listar()) == 1


def test_existing_incompatible_recipe_is_variant_and_not_canonicalized(tmp_path: Path):
    seed_article(tmp_path, "ART-TOMATE", "Tomate")
    seed_article(tmp_path, "ART-CHOCOLATE", "Chocolate")
    RepositorioBibliotecaRecetas601(tmp_path).crear_ficha_tecnica({
        "nombre": "Salsa común", "ingredientes": ["Chocolate"], "cantidades": ["1 kg"],
        "ingredientes_estructurados": [{"nombre_original": "Chocolate", "article_id": "ART-CHOCOLATE"}],
        "elaboracion": "Fundir", "numero_raciones": 10, "tipo": "PRINCIPAL",
    })
    RepositorioEscandallos(tmp_path / "DATOS/db/escandallos_canonicos.json").guardar_todos([
        legacy("REC-LEG-SALSA", "Salsa común", [ingredient("ART-TOMATE", "Tomate")]),
    ])
    service = LegacyRecipeCanonicalizationService(tmp_path)

    case = service.analyze()["casos"][0]

    assert case["estado"] == "POSIBLE_VARIANTE"
    assert case["accion_propuesta"] == "REQUIERE_DECISION"
    assert service.preview(legacy_ids=[], context=context())["canonicalizaciones"] == []
    assert len(RepositorioBibliotecaRecetas601(tmp_path).listar()) == 1


def test_subelaboration_dependencies_are_canonical_and_not_articles(tmp_path: Path):
    seed_article(tmp_path, "ART-A", "Ingrediente A")
    seed_article(tmp_path, "ART-B", "Ingrediente B")
    child = legacy("REC-LEG-B", "Salsa B", [ingredient("ART-B", "Ingrediente B")])
    parent = legacy("REC-LEG-A", "Plato A", [
        ingredient("ART-A", "Ingrediente A"),
        ingredient("REC-LEG-B", "Salsa B", dependency="Salsa B"),
    ])
    RepositorioEscandallos(tmp_path / "DATOS/db/escandallos_canonicos.json").guardar_todos([parent, child])
    service = LegacyRecipeCanonicalizationService(tmp_path)
    preview = service.preview(legacy_ids=None, context=context())

    service.confirm(preview_token=preview["preview_token"], context=context())

    recipes = {item["nombre"]: item for item in RepositorioBibliotecaRecetas601(tmp_path).listar()}
    child_id = recipes["Salsa B"]["id"]
    parent_recipe = recipes["Plato A"]
    dependency_line = next(item for item in parent_recipe["ingredientes_estructurados"] if item["nombre_original"] == "Salsa B")
    assert dependency_line["elaboracion_id"] == child_id
    assert child_id in parent_recipe["otras_dependencias"]
    assert RepositorioProductosMaestro601(tmp_path).obtener_producto("REC-LEG-B") is None
