from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.receta_documentacion_batch_service import RecetaDocumentacionBatchService
from SERVICIOS.receta_documentacion_write_service import RecetaDocumentacionError


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
    def preview(self, *, recipe_id, selected, overwrite_fields, context, proposal_source=None):
        valid, _ = context.validate()
        if not valid or "recetas:write" not in context.scopes:
            raise RecetaDocumentacionError("unauthorized", "El actor no esta autorizado.")
        assert "descripcion" not in selected
        return {"cambios_seleccionados": selected, "preview_token": f"token-{recipe_id}"}
    def confirm(self, *, recipe_id, selected, overwrite_fields, preview_token, context, proposal_source=None):
        self.confirm_calls.append(recipe_id)
        self.repository.items[recipe_id].update(selected)
        self.repository.items[recipe_id]["completitud"] = {"campos_obligatorios_pendientes": []}
        return {"campos_confirmados": list(selected), "lectura_posterior_verificada": True}


def test_batch_relee_filtra_genera_secuencial_y_no_escribe_antes_de_confirm(tmp_path: Path):
    repository = FakeRepository(); individual = FakeRecipeService(repository)
    service = RecetaDocumentacionBatchService(tmp_path, repository=repository, recipe_service=individual)
    before = {key: dict(value) for key, value in repository.items.items()}
    batch = service.start()
    assert batch["ok"] is True
    while batch["progreso"]["analizadas"] < batch["progreso"]["total"]:
        batch = service.next(batch["batch_id"])

    assert batch["recipe_ids"] == ["A", "B", "C"]
    assert individual.proposal_calls == ["A", "B", "C"]
    assert repository.items == before
    assert batch["progreso"] == {"total": 3, "analizadas": 3, "exitosas": 3, "fallidas": 0, "pendientes": 0, "con_propuestas": 2, "necesitan_usuario": 1, "ya_completas": 0, "propuestas": 2}
    assert [item["estado"] for item in batch["cola"]] == ["CON_PROPUESTAS", "CON_PROPUESTAS", "NECESITA_USUARIO"]


def test_batch_seleccion_preview_cero_write_confirm_idempotente_y_relectura(tmp_path: Path):
    repository = FakeRepository(); individual = FakeRecipeService(repository)
    service = RecetaDocumentacionBatchService(tmp_path, repository=repository, recipe_service=individual)
    batch = service.start(recipe_ids=["A", "B", "C", "D", "E"])
    assert batch["recipe_ids"] == ["A", "B", "C", "D", "E"]
    while batch["progreso"]["analizadas"] < batch["progreso"]["total"]: batch = service.next(batch["batch_id"])
    before = {key: dict(value) for key, value in repository.items.items()}
    selected = service.select(batch["batch_id"], {"A": {"elaboracion": "Propuesta A"}, "B": {"elaboracion": "Propuesta B", "descripcion": "No sobrescribir"}})
    repeated_selection = service.select(batch["batch_id"], selected["selecciones"])
    preview = service.preview(batch["batch_id"], context=_context())
    assert repository.items == before
    assert repeated_selection["selecciones"] == selected["selecciones"]
    assert preview["estado"] == "PREVIEW" and preview["preview"]["cambios_a_aplicar"] == 2
    assert preview["preview"]["items"][0]["detalle_cambios"] == [{
        "campo": "elaboracion", "valor_actual": None, "valor_propuesto": "Propuesta A",
        "procedencia": {"fuente": "HOST_AI_API", "origen_externo": "OPENAI_API"},
        "clasificacion": "SELECCION_MASIVA", "sobrescribe": False, "completa": True,
    }]
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


def test_seleccion_explicita_es_frontera_total_y_vacia_no_significa_toda_la_biblioteca(tmp_path: Path):
    repository = FakeRepository(); individual = FakeRecipeService(repository)
    service = RecetaDocumentacionBatchService(tmp_path, repository=repository, recipe_service=individual)

    selected = service.start(recipe_ids=["C", "A", "C", "NO-EXISTE"])
    empty = service.start(recipe_ids=[])

    assert selected["ok"] is True and selected["recipe_ids"] == ["C", "A"]
    assert selected["progreso"]["total"] == 2
    assert empty["ok"] is True and empty["recipe_ids"] == []
    assert individual.proposal_calls == []


def test_endpoint_start_devuelve_200_ok_y_solo_ids_solicitados_sin_invocar_ia(tmp_path: Path):
    repository = FakeRepository(); individual = FakeRecipeService(repository)
    service = RecetaDocumentacionBatchService(tmp_path, repository=repository, recipe_service=individual)
    platform = HostAIPlatformAPI(base_dir=tmp_path)
    platform.facade._recipe_docs_batch_service = service
    client = TestClient(create_app(platform))

    summary = client.get("/api/v1/biblioteca/recetas/completado-ia/resumen")
    response = client.post(
        "/api/v1/biblioteca/recetas/completado-ia/iniciar",
        json={"recipe_ids": ["B", "D"]},
    )
    payload = response.json()
    status = client.get(
        f"/api/v1/biblioteca/recetas/completado-ia/{payload['batch_id']}/estado"
    )

    assert summary.status_code == 200 and summary.json()["ok"] is True
    assert summary.json()["recetas_incompletas"] == 3
    assert response.status_code == 200 and payload["ok"] is True
    assert payload["recipe_ids"] == ["B", "D"] and payload["progreso"]["total"] == 2
    assert status.status_code == 200 and status.json()["ok"] is True
    assert individual.proposal_calls == []


def test_endpoint_seleccion_200_persiste_y_preview_se_solicita_sin_write(tmp_path: Path):
    repository = FakeRepository(); individual = FakeRecipeService(repository)
    service = RecetaDocumentacionBatchService(tmp_path, repository=repository, recipe_service=individual)
    platform = HostAIPlatformAPI(base_dir=tmp_path)
    platform.facade._recipe_docs_batch_service = service
    client = TestClient(create_app(platform))
    batch = service.start(recipe_ids=["A"])
    batch = service.next(batch["batch_id"])
    before = {key: dict(value) for key, value in repository.items.items()}
    url = f"/api/v1/biblioteca/recetas/completado-ia/{batch['batch_id']}"

    selected = client.post(f"{url}/seleccion", json={"selections": {"A": {"elaboracion": "Propuesta A"}}})
    reread = client.get(f"{url}/estado")
    preview = client.post(f"{url}/preview", json={})

    assert selected.status_code == 200 and selected.json()["selecciones"] == {"A": {"elaboracion": "Propuesta A"}}
    assert selected.json()["preview"] is None and selected.json()["datos_reales_modificados"] is False
    assert reread.status_code == 200 and reread.json()["selecciones"] == selected.json()["selecciones"]
    assert preview.status_code == 200 and preview.json()["preview"] is not None
    assert preview.json()["preview"]["cambios_a_aplicar"] == 1
    assert preview.json()["datos_reales_modificados"] is False and repository.items == before


def test_timeout_es_fallo_independiente_continua_reintenta_y_no_duplica(tmp_path: Path):
    repository = FakeRepository()

    class FlakyRecipeService(FakeRecipeService):
        def __init__(self, repository):
            super().__init__(repository)
            self.failed_once = False

        def proposal(self, *, recipe_id, proposed, session_id=""):
            self.proposal_calls.append(recipe_id)
            if recipe_id == "B" and not self.failed_once:
                self.failed_once = True
                raise RecetaDocumentacionError("ai_provider_timeout", "El proveedor IA no respondio a tiempo.")
            return {"ok": True, "receta_id": recipe_id, "datos_propuestos_ia": {"elaboracion": f"Propuesta {recipe_id}"}, "campos_pendientes_no_proponibles": []}

    before = {key: dict(value) for key, value in repository.items.items()}
    individual = FlakyRecipeService(repository)
    service = RecetaDocumentacionBatchService(tmp_path, repository=repository, recipe_service=individual)
    platform = HostAIPlatformAPI(base_dir=tmp_path)
    platform.facade._recipe_docs_batch_service = service
    client = TestClient(create_app(platform))
    batch = client.post("/api/v1/biblioteca/recetas/completado-ia/iniciar", json={"recipe_ids": ["A", "B", "C"]}).json()

    first = client.post(f"/api/v1/biblioteca/recetas/completado-ia/{batch['batch_id']}/siguiente", json={}).json()
    failed = client.post(f"/api/v1/biblioteca/recetas/completado-ia/{batch['batch_id']}/siguiente", json={})
    continued = client.post(f"/api/v1/biblioteca/recetas/completado-ia/{batch['batch_id']}/siguiente", json={}).json()
    reread = client.get(f"/api/v1/biblioteca/recetas/completado-ia/{batch['batch_id']}/estado").json()

    assert failed.status_code == 200 and failed.json()["progreso"]["fallidas"] == 1
    failed_item = next(item for item in failed.json()["resultados"] if item["recipe_id"] == "B")
    assert failed_item["estado"] == "ERROR_PROVIDER"
    assert failed_item["error"]["code"] == "ai_provider_timeout"
    assert continued["progreso"] == {"total": 3, "analizadas": 3, "exitosas": 2, "fallidas": 1, "pendientes": 0, "con_propuestas": 2, "necesitan_usuario": 0, "ya_completas": 0, "propuestas": 2}
    assert continued["estado"] == "PROPUESTAS_LISTAS_CON_ERRORES"
    assert reread["progreso"] == continued["progreso"]
    assert first["resultados"][0]["datos_propuestos_ia"] == {"elaboracion": "Propuesta A"}
    assert repository.items == before

    retried = client.post(
        f"/api/v1/biblioteca/recetas/completado-ia/{batch['batch_id']}/reintentar",
        json={"recipe_id": "B"},
    )
    completed = client.post(f"/api/v1/biblioteca/recetas/completado-ia/{batch['batch_id']}/siguiente", json={}).json()

    assert retried.status_code == 200 and retried.json()["progreso"]["pendientes"] == 1
    assert completed["estado"] == "PROPUESTAS_LISTAS"
    assert completed["progreso"]["propuestas"] == 3
    assert individual.proposal_calls == ["A", "B", "C", "B"]
    assert sum(item["recipe_id"] == "A" for item in completed["resultados"]) == 1
    assert repository.items == before


def test_clasificacion_segura_excluye_criticos_y_exige_seleccion_individual(tmp_path: Path):
    repository = FakeRepository()

    class CriticalRecipeService(FakeRecipeService):
        def proposal(self, *, recipe_id, proposed, session_id=""):
            return {"ok": True, "receta_id": recipe_id, "datos_propuestos_ia": {
                "descripcion": "Salsa cremosa de acabado suave.",
                "elaboracion": "Mezclar y cocinar hasta obtener la textura deseada.",
                "observaciones": "Ajustar la textura al servicio.",
                "alergenos": ["gluten"],
                "vida_util_refrigerado": "48 horas a 4 C",
                "regeneracion": "Alcanzar 70 C en el centro",
                "numero_raciones": 4,
                "tiempo_total": "45 minutos estimados",
            }, "campos_pendientes_no_proponibles": []}

        def preview(self, *, recipe_id, selected, overwrite_fields, context, proposal_source=None):
            return {
                "cambios_seleccionados": dict(selected), "preview_token": f"token-{recipe_id}",
                "receta_antes": dict(self.repository.items[recipe_id]),
                "procedencia_propuesta": dict(proposal_source or {}),
            }

    service = RecetaDocumentacionBatchService(tmp_path, repository=repository, recipe_service=CriticalRecipeService(repository))
    batch = service.start(recipe_ids=["A"])
    batch = service.next(batch["batch_id"])
    item = batch["resultados"][0]

    assert set(item["datos_propuestos_seguros_masivo"]) == {"descripcion", "elaboracion", "observaciones"}
    assert set(item["datos_requieren_revision_individual"]) == {"alergenos", "vida_util_refrigerado", "regeneracion", "numero_raciones", "tiempo_total"}

    selected = service.select(batch["batch_id"], {"A": item["datos_propuestos_ia"]})
    assert set(selected["selecciones"]["A"]) == {"descripcion", "elaboracion", "observaciones"}
    assert "alergenos" not in selected["selecciones"]["A"]
    repeated = service.select(batch["batch_id"], selected["selecciones"])
    before = {key: dict(value) for key, value in repository.items.items()}
    safe_preview = service.preview(batch["batch_id"], context=_context())
    assert repeated["selecciones"] == selected["selecciones"]
    assert set(safe_preview["preview"]["items"][0]["cambios"]) == {"descripcion", "elaboracion", "observaciones"}
    assert {detail["clasificacion"] for detail in safe_preview["preview"]["items"][0]["detalle_cambios"]} == {"SELECCION_MASIVA"}
    assert "alergenos" not in safe_preview["preview"]["items"][0]["cambios"]
    assert repository.items == before

    reviewed = service.select(
        batch["batch_id"], selected["selecciones"],
        {"A": {"alergenos": ["gluten"], "numero_raciones": 4}},
    )
    assert reviewed["selecciones_individuales"]["A"] == {"alergenos": ["gluten"], "numero_raciones": 4}
    assert reviewed["preview"] is None
    reviewed_preview = service.preview(batch["batch_id"], context=_context())
    details = reviewed_preview["preview"]["items"][0]["detalle_cambios"]
    assert {detail["campo"] for detail in details if detail["clasificacion"] == "REVISION_INDIVIDUAL"} == {"alergenos", "numero_raciones"}
    assert repository.items == before


def test_seleccion_segura_de_una_receta_reemplaza_residuales_criticos_y_preview_es_exacto(tmp_path: Path):
    repository = FakeRepository()
    critical = {
        "tiempo_pasivo": "90", "vida_util_refrigerado": "24 horas", "puede_congelarse": False,
        "regeneracion": "Servir fria", "tiempo_total": "120", "puede_refrigerarse": True,
        "tiempo_activo": "30", "alergenos": ["crustaceos"], "vida_util_congelado": "No recomendado",
    }
    safe = {"elaboracion": "Cocer, enfriar y mezclar.", "observaciones": "Mantener refrigerada."}

    class ExactRecipeService(FakeRecipeService):
        def proposal(self, *, recipe_id, proposed, session_id=""):
            return {"datos_propuestos_ia": {**safe, **critical}, "campos_pendientes_no_proponibles": []}

    service = RecetaDocumentacionBatchService(tmp_path, repository=repository, recipe_service=ExactRecipeService(repository))
    batch = service.start(recipe_ids=["A"])
    batch = service.next(batch["batch_id"])
    before = {key: dict(value) for key, value in repository.items.items()}
    service.select(batch["batch_id"], {}, {"A": critical})

    replaced = service.select(batch["batch_id"], {"A": safe}, {})
    preview = service.preview(batch["batch_id"], context=_context())
    repeated = service.select(batch["batch_id"], {"A": safe}, {})

    assert replaced["selecciones"] == {"A": safe} and replaced["selecciones_individuales"] == {}
    assert preview["preview"]["cambios_a_aplicar"] == 2
    assert set(preview["preview"]["items"][0]["cambios"]) == {"elaboracion", "observaciones"}
    assert not set(critical).intersection(preview["preview"]["items"][0]["cambios"])
    assert repeated["selecciones"] == replaced["selecciones"] and repeated["preview"] is None

    reviewed = service.select(batch["batch_id"], repeated["selecciones"], {"A": {"alergenos": ["crustaceos"]}})
    reviewed_preview = service.preview(batch["batch_id"], context=_context())
    assert reviewed["selecciones_individuales"] == {"A": {"alergenos": ["crustaceos"]}}
    assert reviewed_preview["preview"]["cambios_a_aplicar"] == 3
    assert repository.items == before


def test_dataset_controlado_30_recetas_83_seguras_257_criticas_preview_solo_83(tmp_path: Path):
    repository = FakeRepository()
    repository.items = {
        f"R{index:02d}": {"id": f"R{index:02d}", "nombre": f"Receta {index:02d}", "completitud": {"campos_obligatorios_pendientes": ["Documentacion"]}}
        for index in range(30)
    }
    critical_fields = [
        "alergenos", "vida_util_refrigerado", "vida_util_congelado", "puede_congelarse",
        "puede_refrigerarse", "regeneracion", "tiempo_activo", "tiempo_pasivo", "tiempo_total",
    ]

    class DatasetRecipeService(FakeRecipeService):
        def proposal(self, *, recipe_id, proposed, session_id=""):
            index = int(recipe_id[1:])
            safe = {"elaboracion": f"Elaboracion {index}", "observaciones": f"Observaciones {index}"}
            if index < 23:
                safe["descripcion"] = f"Descripcion {index}"
            critical_count = 9 if index < 17 else 8
            critical = {field: f"Valor {field} {index}" for field in critical_fields[:critical_count]}
            critical["alergenos"] = ["gluten"]
            return {"datos_propuestos_ia": {**safe, **critical}, "campos_pendientes_no_proponibles": []}

        def preview(self, *, recipe_id, selected, overwrite_fields, context, proposal_source=None):
            return {
                "cambios_seleccionados": dict(selected), "preview_token": f"token-{recipe_id}",
                "receta_antes": dict(self.repository.items[recipe_id]),
                "procedencia_propuesta": dict(proposal_source or {}),
            }

    service = RecetaDocumentacionBatchService(tmp_path, repository=repository, recipe_service=DatasetRecipeService(repository))
    batch = service.start(recipe_ids=list(repository.items))
    while batch["progreso"]["pendientes"]:
        batch = service.next(batch["batch_id"])
    selections = {item["recipe_id"]: item["datos_propuestos_seguros_masivo"] for item in batch["resultados"]}
    before = {key: dict(value) for key, value in repository.items.items()}
    selected = service.select(batch["batch_id"], selections, {})
    preview = service.preview(batch["batch_id"], context=_context())

    assert batch["progreso"] == {"total": 30, "analizadas": 30, "exitosas": 30, "fallidas": 0, "pendientes": 0, "con_propuestas": 30, "necesitan_usuario": 0, "ya_completas": 0, "propuestas": 340}
    assert sum(len(fields) for fields in selected["selecciones"].values()) == 83
    assert selected["selecciones_individuales"] == {}
    assert preview["preview"]["recetas_afectadas"] == 30 and preview["preview"]["cambios_a_aplicar"] == 83
    assert repository.items == before


def test_resumen_masivo_y_excepciones_se_calculan_sin_abrir_recetas(tmp_path: Path):
    repository = FakeRepository()

    class SummaryRecipeService(FakeRecipeService):
        def proposal(self, *, recipe_id, proposed, session_id=""):
            ready = recipe_id == "A"
            return {
                "datos_propuestos_ia": {"elaboracion": f"Propuesta {recipe_id}", "alergenos": ["gluten"]},
                "datos_propuestos_seguros_masivo": {"elaboracion": f"Propuesta {recipe_id}"},
                "campos_pendientes_no_proponibles": [],
                "metadatos_propuestas": {"elaboracion": {"confianza": 0.5 if recipe_id == "B" else 0.9}},
                "completitud": {
                    "production_ready_provisional": ready,
                    "production_ready_confirmed": False,
                    "pendientes": [] if ready else ["unidad_tanda"],
                    "no_aplica": ["regeneracion"] if ready else [],
                    "resolucion_campos": {},
                },
            }

    service = RecetaDocumentacionBatchService(
        tmp_path, repository=repository, recipe_service=SummaryRecipeService(repository),
    )
    batch = service.start(recipe_ids=["A", "B"])
    while batch["progreso"]["pendientes"]:
        batch = service.next(batch["batch_id"])

    assert batch["resumen_masivo"]["recetas_procesadas"] == 2
    assert batch["resumen_masivo"]["production_ready_provisional"] == 1
    assert batch["resumen_masivo"]["criticos_pendientes"] == 2
    assert batch["resumen_masivo"]["baja_confianza"] == 1
    assert batch["resumen_masivo"]["no_aplica"] == 1
    assert batch["resultados"][0]["estado_operativo"] == "PRODUCTION_READY_PROVISIONAL"
    assert batch["resultados"][1]["excepciones"]["no_production_ready"] is True


def test_reintentar_todas_las_fallidas_respeta_limite_y_conserva_exitos(tmp_path: Path):
    repository = FakeRepository()

    class FailOnceEach(FakeRecipeService):
        def __init__(self, repository):
            super().__init__(repository)
            self.attempts = {}

        def proposal(self, *, recipe_id, proposed, session_id=""):
            self.proposal_calls.append(recipe_id)
            self.attempts[recipe_id] = self.attempts.get(recipe_id, 0) + 1
            if self.attempts[recipe_id] == 1:
                raise RecetaDocumentacionError("ai_provider_connection", "Conexion temporal no disponible.")
            return {"datos_propuestos_ia": {"elaboracion": f"Propuesta {recipe_id}"}, "campos_pendientes_no_proponibles": []}

    individual = FailOnceEach(repository)
    service = RecetaDocumentacionBatchService(tmp_path, repository=repository, recipe_service=individual)
    batch = service.start(recipe_ids=["A", "B"])
    batch = service.next(batch["batch_id"])
    batch = service.next(batch["batch_id"])
    assert batch["progreso"]["fallidas"] == 2

    batch = service.retry_failed(batch["batch_id"])
    assert batch["progreso"]["pendientes"] == 2
    batch = service.next(batch["batch_id"])
    batch = service.next(batch["batch_id"])

    assert batch["estado"] == "PROPUESTAS_LISTAS"
    assert batch["progreso"]["propuestas"] == 2
    assert individual.proposal_calls == ["A", "B", "A", "B"]

    class AlwaysFail(FakeRecipeService):
        def proposal(self, *, recipe_id, proposed, session_id=""):
            raise RecetaDocumentacionError("ai_provider_timeout", "Timeout.")

    limited = RecetaDocumentacionBatchService(tmp_path, repository=repository, recipe_service=AlwaysFail(repository))
    limited_batch = limited.start(recipe_ids=["A"])
    for attempt in range(3):
        limited_batch = limited.next(limited_batch["batch_id"])
        if attempt < 2:
            limited_batch = limited.retry(limited_batch["batch_id"], "A")
    assert limited_batch["resultados"][0]["reintento_disponible"] is False
    with pytest.raises(RecetaDocumentacionError) as exhausted:
        limited.retry(limited_batch["batch_id"], "A")
    assert exhausted.value.code == "provider_retry_limit"


def test_preview_y_confirm_masivos_exigen_autorizacion_y_preview_valido(tmp_path: Path):
    repository = FakeRepository(); individual = FakeRecipeService(repository)
    service = RecetaDocumentacionBatchService(tmp_path, repository=repository, recipe_service=individual)
    batch = service.start(recipe_ids=["A"])
    batch = service.next(batch["batch_id"])
    service.select(batch["batch_id"], {"A": {"elaboracion": "Propuesta A"}})
    unauthorized = AuthorizedExecutionContext("REQ", "", "LOCAL", (), frozenset())

    with pytest.raises(RecetaDocumentacionError) as denied:
        service.preview(batch["batch_id"], context=unauthorized)
    with pytest.raises(RecetaDocumentacionError) as stale:
        service.confirm(batch["batch_id"], fingerprint="", context=_context())

    assert denied.value.code == "unauthorized"
    assert stale.value.code == "stale_or_invalid_preview"
    assert individual.confirm_calls == []
