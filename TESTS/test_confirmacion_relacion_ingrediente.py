import json
from pathlib import Path

import pytest

from CORE.entidades.escandallo import Escandallo
from CORE.entidades.ingrediente import Ingrediente
from CORE.entidades.receta import Receta
from SERVICIOS.confirmacion_relacion_ingrediente_service import ConfirmacionRelacionIngredienteService, ErrorConfirmacionRelacionIngrediente
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos


def _context() -> AuthorizedExecutionContext:
    return AuthorizedExecutionContext("REQ", "CHEF", "LOCAL", ("chef",), frozenset({"recetas:write"}))


def _service(base: Path) -> ConfirmacionRelacionIngredienteService:
    repo = RepositorioEscandallos(base / "DATOS" / "db" / "escandallos_canonicos.json")
    repo.guardar_todos([Escandallo(Receta("REC-SALSA", "Salsa", 4, "u", [Ingrediente("ING-PATATA", "Patata Monalisa", 1, "kg")]), 0)])
    articles = base / "DATOS" / "db" / "articulos.json"
    articles.parent.mkdir(parents=True, exist_ok=True)
    articles.write_text(json.dumps([{"codigo": "ART000238", "nombre": "Patata Monalisa", "unidad_base": "kg", "precio": 2}]), encoding="utf-8")
    return ConfirmacionRelacionIngredienteService(base, repository=repo)


def test_preview_no_escribe_y_confirmacion_es_idempotente(tmp_path: Path) -> None:
    service = _service(tmp_path)
    path = tmp_path / "DATOS" / "db" / "escandallos_canonicos.json"
    before = path.read_bytes()
    preview = service.preview(recipe_id="REC-SALSA", ingredient_index=0, article_id="ART000238", context=_context())
    assert preview["datos_reales_modificados"] is False and path.read_bytes() == before
    confirmed = service.confirm(recipe_id="REC-SALSA", ingredient_index=0, article_id="ART000238", preview_token=preview["preview_token"], context=_context())
    repeated_preview = service.preview(recipe_id="REC-SALSA", ingredient_index=0, article_id="ART000238", context=_context())
    repeated = service.confirm(recipe_id="REC-SALSA", ingredient_index=0, article_id="ART000238", preview_token=repeated_preview["preview_token"], context=_context())
    assert confirmed["datos_reales_modificados"] is True
    assert repeated["idempotente"] is True


def test_preview_caduca_si_cambia_ingrediente(tmp_path: Path) -> None:
    service = _service(tmp_path)
    preview = service.preview(recipe_id="REC-SALSA", ingredient_index=0, article_id="ART000238", context=_context())
    recipe = service.repository.listar()[0]
    recipe.receta.ingredientes[0].nombre = "Patata nueva"
    service.repository.upsert(recipe)
    with pytest.raises(ErrorConfirmacionRelacionIngrediente) as exc:
        service.confirm(recipe_id="REC-SALSA", ingredient_index=0, article_id="ART000238", preview_token=preview["preview_token"], context=_context())
    assert exc.value.code == "stale_or_invalid_preview"