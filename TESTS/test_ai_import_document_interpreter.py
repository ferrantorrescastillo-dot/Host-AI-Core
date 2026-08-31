from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from SERVICIOS.ai_import_document_interpreter import AIImportDocumentInterpreter, AIImportInterpretationError
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.importador_inteligente_biblioteca import ImportDocumentService
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601
from CORE.entidades.escandallo import Escandallo
from CORE.entidades.ingrediente import Ingrediente
from CORE.entidades.receta import Receta
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos


def _file(text: str = "Campo raro,Otro\nChalota,1\n") -> dict:
    raw = text.encode()
    return {"nombre": "complejo.csv", "tipo_mime": "text/csv",
            "contenido_base64": base64.b64encode(raw).decode(), "texto": text}


def _package() -> dict:
    return {
        "schema": "hostai.import.package", "version": "0.1", "metadata": {"extractor": "FAKE"},
        "recipes": [{"name": "Salsa naranja", "ingredients": [{"name": "Chalota", "quantity": 1, "unit": "kg"}],
                     "yield": 1, "procedure": ["Reducir"],
                     "occurrences": [{"sheet": "A", "row": 1}, {"sheet": "B", "row": 2},
                                     {"sheet": "C", "row": 3}, {"sheet": "D", "row": 4}]}],
        "articles": [{"name": "Chalota", "unit": "kg"}], "suppliers": [],
        "menus": [{"name": "TAPA", "kind": "CONTEXT"}, {"name": "MENU CALÇOTADA", "kind": "MENU"}],
        "relations": [], "ambiguities": [{"type": "NO_SE", "name": "Rendimiento", "reason": "No informado"}],
        "variant_groups": [{"name": "Patatas Bravas", "versions": [
            {"ingredients": [{"name": "Patata", "quantity": 1, "unit": "kg"}]},
            {"ingredients": [{"name": "Patata", "quantity": 2, "unit": "kg"}, {"name": "Salsa", "quantity": 1, "unit": "kg"}]},
        ]}],
    }


def _filesystem_snapshot(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        snapshot[f"dir:{relative}" if path.is_dir() else f"file:{relative}"] = (
            "DIR" if path.is_dir() else hashlib.sha256(path.read_bytes()).hexdigest()
        )
    return snapshot


class FakeEngine:
    default_provider = "FAKE"
    def __init__(self, package=None, errors=None):
        self.package = package if package is not None else _package(); self.errors = errors or []; self.calls = 0; self.requests = []
    def crear_consulta(self, **kwargs): self.requests.append(kwargs); return kwargs
    def ejecutar(self, request):
        self.calls += 1
        return SimpleNamespace(respuesta={"package": self.package}, errores=self.errors,
                               usage={"input_tokens": 10}, cost_breakdown={"total_cost": "0.001"})


def test_interpreter_uses_canonical_engine_contract_schema_and_fingerprint(tmp_path: Path):
    fake = FakeEngine()
    interpreter = AIImportDocumentInterpreter(tmp_path, engine_factory=lambda _: fake)
    first = interpreter.interpret({"archivos": [_file()]})
    second = interpreter.interpret({"archivos": [_file()]})
    sent = fake.requests[0]["datos_enviados"]
    assert first["package"]["schema"] == "hostai.import.package"
    assert sent["schema_salida"]["properties"]["version"]["const"] == "0.1"
    assert sent["documento_estructural"]["summary"]["regions"] == 1
    assert first["fingerprint"] == second["fingerprint"]
    assert second["cache_hit"] is True and fake.calls == 1


@pytest.mark.parametrize("package", [
    {"schema": "otro", "version": "0.1", "metadata": {}},
    {**_package(), "stock": 999},
    {**_package(), "recipes": [{"name": "X", "article_id": "ART-FALSO"}]},
    {**_package(), "articles": [{"name": "X", "precio_real": 5}]},
])
def test_invalid_or_unsafe_ai_output_is_rejected(package, tmp_path: Path):
    interpreter = AIImportDocumentInterpreter(tmp_path, engine_factory=lambda _: FakeEngine(package))
    with pytest.raises(AIImportInterpretationError, match="package seguro"):
        interpreter.interpret({"archivos": [_file()]})
    assert not (tmp_path / "DATOS").exists()


def test_ai_package_goes_through_existing_matchers_and_keeps_semantics(tmp_path: Path):
    product = RepositorioProductosMaestro601(tmp_path).crear_producto({"nombre": "Chalota", "unidad_base": "kg"})
    recipe_repo = RepositorioBibliotecaRecetas601(tmp_path)
    recipe_repo.crear_ficha_tecnica({"nombre": "Salsa de naranja", "ingredientes": ["Chalota"],
                                     "cantidades": ["1 kg"], "elaboracion": "Reducir",
                                     "numero_raciones": 1, "tipo": "SALSA"})
    fake = FakeEngine()
    interpreter = AIImportDocumentInterpreter(tmp_path, engine_factory=lambda _: fake)
    result = ImportDocumentService(tmp_path, ai_document_interpreter=interpreter).import_document({
        "archivos": [_file()], "analizar_documento_con_ia": True,
    })
    session = result["importacion"]
    assert session["resolucion_identidad"]["articulos"]["ya_existentes"] == 1
    assert session["borrador"]["catalogo"]["articulos"][0]["article_id"] == product["codigo"]
    assert session["resolucion_identidad"]["recetas"]["ya_canonicas"] == 1
    assert all(item["name"] != "TAPA" or item["kind"] != "RECETA" for item in session["documento"]["entidades"])
    assert any(item["fields"].get("tipo") == "MENU" for item in session["documento"]["entidades"])
    assert session["resolucion_identidad"]["variantes"]["grupos"] == 1
    assert len(session["analisis_restaurante"]["decisiones_usuario"]) == 1
    assert session["analisis_restaurante"]["ai_import"]["used"] is True
    assert not (tmp_path / "DATOS/db/biblioteca_importaciones_web.json").exists()


def test_ai_failure_allows_basic_fallback_and_never_runs_without_opt_in(tmp_path: Path):
    fake = FakeEngine(errors=["timeout"])
    interpreter = AIImportDocumentInterpreter(tmp_path, engine_factory=lambda _: fake)
    service = ImportDocumentService(tmp_path, ai_document_interpreter=interpreter)
    basic = service.import_document({"archivos": [_file()]})
    assert basic["ok"] is True and fake.calls == 0
    failed = service.import_document({"archivos": [_file()], "analizar_documento_con_ia": True})
    assert failed["ok"] is False and failed["error"]["code"] == "ai_import_interpretation_failed"
    fallback = service.import_document({"archivos": [_file()]})
    assert fallback["ok"] is True and fake.calls == 1
    assert not (tmp_path / "DATOS/db/biblioteca_importaciones_web.json").exists()


def test_free_known_or_basic_path_exposes_decision_without_ai_call(tmp_path: Path):
    fake = FakeEngine()
    interpreter = AIImportDocumentInterpreter(tmp_path, engine_factory=lambda _: fake)
    session = ImportDocumentService(tmp_path, ai_document_interpreter=interpreter).import_document({
        "archivos": [_file("Receta,Ingrediente,Cantidad,Unidad\nSalsa,Tomate,1,kg\n")]
    })["importacion"]
    assert session["analisis_restaurante"]["ai_import"]["used"] is False
    assert fake.calls == 0


def test_post_ai_recipe_uses_existing_legacy_bridge_without_reimplementing_it(tmp_path: Path):
    RepositorioProductosMaestro601(tmp_path).crear_producto({
        "codigo": "ART-CHALOTA", "nombre": "Chalota", "unidad_base": "kg",
    })
    legacy_ingredient = Ingrediente(
        codigo="ART-CHALOTA", nombre="Chalota", cantidad=1, unidad="kg",
        articulo_id="ART-CHALOTA", metadata={"tipo": "ARTICULO"},
    )
    RepositorioEscandallos(tmp_path / "DATOS/db/escandallos_canonicos.json").guardar_todos([
        Escandallo(Receta("REC-LEG-NARANJA", "Salsa naranja", 1, "u", [legacy_ingredient]), coste_total=1),
    ])
    fake = FakeEngine()
    session = ImportDocumentService(
        tmp_path,
        ai_document_interpreter=AIImportDocumentInterpreter(tmp_path, engine_factory=lambda _: fake),
    ).import_document({"archivos": [_file()], "analizar_documento_con_ia": True})["importacion"]

    legacy = session["resolucion_identidad"]["recetas"]
    assert legacy["ya_conocidas_legacy"] == 1
    assert legacy["grupos"]["ya_conocidas_legacy"][0]["legacy_source_ids"] == ["REC-LEG-NARANJA"]
    assert RepositorioBibliotecaRecetas601(tmp_path).listar() == []


def test_structural_document_is_globally_bounded(tmp_path: Path):
    rows = "Campo,Otro\n" + "\n".join(f"Fila {index},{index}" for index in range(1000))
    fake = FakeEngine()
    result = AIImportDocumentInterpreter(tmp_path, engine_factory=lambda _: fake).interpret({
        "archivos": [_file(rows)],
    })
    assert result["structural_summary"]["rows_sent"] <= AIImportDocumentInterpreter.MAX_ROWS_TOTAL
    assert all(
        len(region["rows"]) <= AIImportDocumentInterpreter.MAX_ROWS_PER_REGION
        for region in fake.requests[0]["datos_enviados"]["documento_estructural"]["regions"]
    )


@pytest.mark.parametrize("with_ai", [False, True])
def test_analyze_and_preview_do_not_persist_even_on_empty_base(tmp_path: Path, with_ai: bool):
    before = _filesystem_snapshot(tmp_path)
    fake = FakeEngine()
    service = ImportDocumentService(
        tmp_path,
        ai_document_interpreter=AIImportDocumentInterpreter(tmp_path, engine_factory=lambda _: fake),
    )
    payload = {"archivos": [_file()]}
    if with_ai:
        payload["analizar_documento_con_ia"] = True
    analyzed = service.import_document(payload)
    after_analyze = _filesystem_snapshot(tmp_path)
    import_id = analyzed["importacion"]["documento"]["id"]
    preview = service.get_draft(import_id)

    assert analyzed["ok"] is True and preview["ok"] is True
    assert fake.calls == int(with_ai)
    assert after_analyze == before
    assert _filesystem_snapshot(tmp_path) == before


def test_analyze_does_not_modify_existing_repository_bytes(tmp_path: Path):
    repository = RepositorioProductosMaestro601(tmp_path)
    repository.crear_producto({"codigo": "ART-EXISTENTE", "nombre": "Chalota", "unidad_base": "kg"})
    before = _filesystem_snapshot(tmp_path)

    result = ImportDocumentService(tmp_path).import_document({"archivos": [_file()]})

    assert result["ok"] is True
    assert _filesystem_snapshot(tmp_path) == before
