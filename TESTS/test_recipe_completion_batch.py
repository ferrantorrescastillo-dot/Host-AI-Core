from pathlib import Path

from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.receta_documentacion_batch_service import RecetaDocumentacionBatchService


def _context():
    return AuthorizedExecutionContext("REQ", "CHEF", "LOCAL", ("chef",), frozenset({"recetas:write"}))


class FakeRepository:
    def __init__(self):
        self.items = {
            "A": {"id": "A", "nombre": "A", "completitud": {"campos_obligatorios_pendientes": ["Elaboración paso a paso"]}},
            "B": {"id": "B", "nombre": "B", "descripcion": "Humana", "completitud": {"campos_obligatorios_pendientes": ["Elaboración paso a paso"]}},
            "C": {"id": "C", "nombre": "C", "completitud": {"campos_obligatorios_pendientes": ["Rendimiento"]}},
            "D": {"id": "D", "nombre": "D", "completitud": {"campos_obligatorios_pendientes": []}},
            "E": {"id": "E", "nombre": "E", "elaboracion": "IA previa", "completitud": {"campos_obligatorios_pendientes": []}},
        }

    def listar(self): return list(self.items.values())
    def obtener(self, recipe_id): return self.items.get(recipe_id)


class FakeRecipeService:
    def __init__(self, repository): self.repository = repository; self.proposal_calls = []; self.confirm_calls = []
    def proposal(self, *, recipe_id, proposed, session_id=""):
        self.proposal_calls.append(recipe_id)
        if recipe_id == "C": proposals, manual = {}, ["Rendimiento"]
        else: proposals, manual = {"elaboracion": f"Propuesta {recipe_id}"}, []
        return {"ok": True, "receta_id": recipe_id, "datos_propuestos_ia": proposals, "campos_pendientes_no_proponibles": manual}
    def preview(self, *, recipe_id, selected, overwrite_fields, context):
        assert "descripcion" not in selected
        return {"cambios_seleccionados": selected, "preview_token": f"token-{recipe_id}"}
    def confirm(self, *, recipe_id, selected, overwrite_fields, preview_token, context):
        self.confirm_calls.append(recipe_id)
        self.repository.items[recipe_id].update(selected)
        self.repository.items[recipe_id]["completitud"] = {"campos_obligatorios_pendientes": []}
        return {"campos_confirmados": list(selected), "lectura_posterior_verificada": True}


def test_batch_relee_filtra_genera_secuencial_y_no_escribe_antes_de_confirm(tmp_path: Path):
    repository = FakeRepository(); individual = FakeRecipeService(repository)
    service = RecetaDocumentacionBatchService(tmp_path, repository=repository, recipe_service=individual)
    before = {key: dict(value) for key, value in repository.items.items()}
    batch = service.start()
    while batch["progreso"]["analizadas"] < batch["progreso"]["total"]:
        batch = service.next(batch["batch_id"])

    assert batch["recipe_ids"] == ["A", "B", "C"]
    assert individual.proposal_calls == ["A", "B", "C"]
    assert repository.items == before
    assert batch["progreso"] == {"total": 3, "analizadas": 3, "con_propuestas": 2, "necesitan_usuario": 1, "ya_completas": 0, "propuestas": 2}


def test_batch_seleccion_preview_cero_write_confirm_idempotente_y_relectura(tmp_path: Path):
    repository = FakeRepository(); individual = FakeRecipeService(repository)
    service = RecetaDocumentacionBatchService(tmp_path, repository=repository, recipe_service=individual)
    batch = service.start(recipe_ids=["A", "B", "C", "D", "E"])
    while batch["progreso"]["analizadas"] < batch["progreso"]["total"]: batch = service.next(batch["batch_id"])
    before = {key: dict(value) for key, value in repository.items.items()}
    service.select(batch["batch_id"], {"A": {"elaboracion": "Propuesta A"}, "B": {"elaboracion": "Propuesta B", "descripcion": "No sobrescribir"}})
    preview = service.preview(batch["batch_id"], context=_context())
    assert repository.items == before
    result = service.confirm(batch["batch_id"], fingerprint=preview["preview"]["fingerprint"], context=_context())
    repeated = service.confirm(batch["batch_id"], fingerprint=preview["preview"]["fingerprint"], context=_context())
    assert individual.confirm_calls == ["A", "B"]
    assert result["aplicadas"][0]["lectura_posterior_verificada"] is True
    assert repeated["idempotente"] is True
    assert repository.items["B"]["descripcion"] == "Humana"


def test_cancelar_no_escribe(tmp_path: Path):
    repository = FakeRepository(); service = RecetaDocumentacionBatchService(tmp_path, repository=repository, recipe_service=FakeRecipeService(repository))
    before = {key: dict(value) for key, value in repository.items.items()}
    batch = service.start(); cancelled = service.cancel(batch["batch_id"])
    assert cancelled["estado"] == "CANCELADO" and repository.items == before
