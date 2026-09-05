import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.confirmacion_procedimiento_receta_service import ConfirmacionProcedimientoRecetaService
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.receta_completion_workflow import RecipeCompletionWorkflow
from SERVICIOS.receta_documentacion_write_service import HostAIRecipeProposalGenerator, RecetaDocumentacionError, RecetaDocumentacionWriteService
from SERVICIOS.catalog_crud_write_service import CatalogCrudWriteService
from SERVICIOS.host_ai_engine.models import HostAIProviderResult


def _context() -> AuthorizedExecutionContext:
    return AuthorizedExecutionContext("REQ", "CHEF", "LOCAL", ("chef",), frozenset({"recetas:write"}))


def _recipe(base: Path) -> str:
    path = base / "DATOS" / "db" / "biblioteca_recetas_601.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"version_modelo": "6.0.1", "recetas": [{
        "id": "REC601-000001", "codigo": "SALSA-NATA", "nombre": "Salsa de nata",
        "familia": "salsas", "tipo": "salsa", "numero_raciones": 4,
        "ingredientes": ["Nata", "Patata Monalisa"], "cantidades": ["1 l", "1 kg"],
        "elaboracion": "", "tiempo_elaboracion": "", "conservacion": "", "alergenos": [],
        "observaciones": "", "fotografia": "", "estado": "PENDIENTE_DE_COMPLETAR",
        "version": 1, "creado_en": "2026-01-01T00:00:00", "actualizado_en": "2026-01-01T00:00:00",
    }]}), encoding="utf-8")
    return "REC601-000001"


def test_procedimiento_ia_se_previsualiza_y_confirma_de_forma_idempotente(tmp_path: Path) -> None:
    recipe_id = _recipe(tmp_path)
    service = ConfirmacionProcedimientoRecetaService(tmp_path)
    proposal = "Propuesta de IA: calentar la nata suavemente, incorporar la patata cocida y triturar hasta obtener una salsa homogénea."
    before = (tmp_path / "DATOS" / "db" / "biblioteca_recetas_601.json").read_bytes()

    preview = service.preview(recipe_id=recipe_id, procedure=proposal, context=_context())
    assert preview["origen_propuesta"] == "IA" and preview["datos_reales_modificados"] is False
    assert (tmp_path / "DATOS" / "db" / "biblioteca_recetas_601.json").read_bytes() == before
    saved = service.confirm(recipe_id=recipe_id, procedure=proposal, preview_token=preview["preview_token"], context=_context())
    repeated = service.confirm(recipe_id=recipe_id, procedure=proposal, preview_token=service.preview(recipe_id=recipe_id, procedure=proposal, context=_context())["preview_token"], context=_context())

    assert saved["datos_reales_modificados"] is True
    assert repeated["idempotente"] is True


def test_investigacion_no_inventa_precio_ni_relaciona_ambiguedades(tmp_path: Path) -> None:
    recipe_id = _recipe(tmp_path)
    db = tmp_path / "DATOS" / "db"
    (db / "articulos.json").write_text('[{"codigo":"ART-NATA-1","nombre":"Nata cocinar","precio":null},{"codigo":"ART-NATA-2","nombre":"Nata montar","precio":null},{"codigo":"ART-PATATA","nombre":"Patata Monalisa","precio":null}]', encoding="utf-8")
    result = RecipeCompletionWorkflow(tmp_path).investigate(recipe_id)

    assert result.procedure_proposal.startswith("Propuesta de IA")
    assert any(item["ingrediente"] == "Nata" for item in result.completeness["AMBIGUO"])
    assert any(item.get("articulo") == "Patata Monalisa" for item in result.completeness["FALTA"])
    assert "precio real" in result.summary


def test_documentacion_ia_persiste_procedencia_historial_y_relectura(tmp_path: Path) -> None:
    recipe_id = _recipe(tmp_path)
    service = RecetaDocumentacionWriteService(tmp_path)
    selected = {"elaboracion": "Pochar, triturar y enfriar de forma controlada."}

    preview = service.preview(recipe_id=recipe_id, selected=selected, overwrite_fields=[], context=_context())
    saved = service.confirm(recipe_id=recipe_id, selected=selected, overwrite_fields=[], preview_token=preview["preview_token"], context=_context())
    repeated = service.confirm(recipe_id=recipe_id, selected=selected, overwrite_fields=[], preview_token=preview["preview_token"], context=_context())
    reread = RepositorioBibliotecaRecetas601(tmp_path).obtener(recipe_id)

    assert saved["lectura_posterior_verificada"] is True
    assert repeated["idempotente"] is True
    assert reread["procedencia_campos"]["elaboracion"]["tipo"] == "IA"
    assert reread["historial_procedencia"][-1]["origen_nuevo"] == "IA"
    assert "Procedimiento" not in reread["completitud"]["campos_obligatorios_pendientes"]


def test_edicion_humana_posterior_conserva_historial_ia(tmp_path: Path) -> None:
    recipe_id = _recipe(tmp_path)
    context = _context()
    ai = RecetaDocumentacionWriteService(tmp_path)
    selected = {"elaboracion": "Propuesta IA revisable."}
    preview = ai.preview(recipe_id=recipe_id, selected=selected, overwrite_fields=[], context=context)
    ai.confirm(recipe_id=recipe_id, selected=selected, overwrite_fields=[], preview_token=preview["preview_token"], context=context)

    human = CatalogCrudWriteService(tmp_path)
    edit = human.preview(domain="RECETA", operation="MODIFICAR", entity_id=recipe_id, session_id="S1", context=context, payload={"elaboracion": "Procedimiento validado por el chef."})
    human.confirm(preview_token=edit["preview_token"], session_id="S1", context=context)
    reread = RepositorioBibliotecaRecetas601(tmp_path).obtener(recipe_id)

    assert reread["elaboracion"] == "Procedimiento validado por el chef."
    assert reread["procedencia_campos"]["elaboracion"]["tipo"] == "USUARIO"
    assert [item["origen_nuevo"] for item in reread["historial_procedencia"][-2:]] == ["IA", "USUARIO"]


def test_generador_inyectado_recibe_faltantes_reales_y_no_escribe(tmp_path: Path) -> None:
    recipe_id = _recipe(tmp_path)
    calls = []

    class FakeGenerator:
        def generate(self, *, recipe, missing_fields, allowed_fields):
            calls.append({"recipe": recipe, "missing_fields": missing_fields, "allowed_fields": allowed_fields})
            return {"elaboracion": "Preparar, cocinar y verificar el punto.", "precio": 99}

    path = tmp_path / "DATOS" / "db" / "biblioteca_recetas_601.json"
    before = path.read_bytes()
    result = RecetaDocumentacionWriteService(tmp_path, generator=FakeGenerator()).proposal(recipe_id=recipe_id, proposed={})

    assert calls and "Elaboración paso a paso" in calls[0]["missing_fields"]
    assert result["datos_propuestos_ia"] == {
        "elaboracion": "Preparar, cocinar y verificar el punto.", "rendimiento": 4.0,
    }
    assert result["metadatos_propuestas"]["rendimiento"]["origen"] == "CALCULADO"
    assert result["generado_ahora"] is True and result["datos_reales_modificados"] is False
    assert path.read_bytes() == before


def test_production_ready_provisional_distingue_propuestas_de_confirmacion(tmp_path: Path) -> None:
    recipe_id = _recipe(tmp_path)
    service = RecetaDocumentacionWriteService(tmp_path)
    proposed = {
        "tipo_elaboracion": "salsa",
        "rendimiento": 4,
        "unidad_rendimiento": "raciones",
        "cantidad_por_racion": {"cantidad": 250, "unidad": "ml"},
        "ingredientes_estructurados": [
            {"nombre_original": "Nata", "cantidad": 1, "unidad": "l", "cantidad_normalizada": 1, "unidad_normalizada": "l"},
            {"nombre_original": "Patata Monalisa", "cantidad": 1, "unidad": "kg", "cantidad_normalizada": 1, "unidad_normalizada": "kg"},
        ],
        "tiempo_activo": "20 minutos",
        "tiempo_pasivo": {"estado": "NO_APLICA", "motivo": "No tiene fase pasiva."},
        "tiempo_total": "20 minutos",
        "produccion_maxima": 4,
        "unidad_tanda": "raciones",
        "rendimiento_por_tanda": 4,
        "personal_recomendado": {"personas": 1, "rol": "cocinero"},
        "recursos_necesarios": ["cazo", "batidora"],
        "puede_refrigerarse": False,
        "puede_congelarse": False,
        "conservacion": "Servicio inmediato.",
        "regeneracion": {"estado": "NO_APLICA", "motivo": "Servicio inmediato."},
    }
    before = (tmp_path / "DATOS" / "db" / "biblioteca_recetas_601.json").read_bytes()

    result = service.proposal(recipe_id=recipe_id, proposed=proposed)
    coverage = result["completitud"]

    assert coverage["production_ready_provisional"] is True
    assert coverage["production_ready_confirmed"] is False
    assert coverage["production_ready"]["bloqueos_provisionales"] == []
    assert coverage["resolucion_campos"]["rendimiento"]["estado"] == "RESUELTO_IA"
    assert coverage["resolucion_campos"]["regeneracion"]["estado"] == "NO_APLICA"
    assert (tmp_path / "DATOS" / "db" / "biblioteca_recetas_601.json").read_bytes() == before

    preview = service.preview(
        recipe_id=recipe_id, selected=result["datos_propuestos_ia"], overwrite_fields=[], context=_context(),
        proposal_metadata_by_field=result["metadatos_propuestas"],
    )
    service.confirm(
        recipe_id=recipe_id, selected=result["datos_propuestos_ia"], overwrite_fields=[],
        preview_token=preview["preview_token"], context=_context(),
        proposal_metadata_by_field=result["metadatos_propuestas"],
    )
    confirmed = service._completion_projection(
        RepositorioBibliotecaRecetas601(tmp_path).obtener(recipe_id), {}, {},
    )
    assert confirmed["production_ready_provisional"] is True
    assert confirmed["production_ready_confirmed"] is True


def test_rendimiento_y_otros_datos_criticos_embebidos_se_bloquean_sin_escribir(tmp_path: Path) -> None:
    recipe_id = _recipe(tmp_path)

    class EmbeddedCriticalGenerator:
        def generate(self, *, recipe, missing_fields, allowed_fields):
            return {
                "descripcion": "Salsa cremosa. Rinde 4 raciones.",
                "observaciones": "Vida util: conservar durante 48 horas.",
                "elaboracion": "Cocinar hasta que las piezas alcancen 70 °C en el centro.",
            }

    path = tmp_path / "DATOS" / "db" / "biblioteca_recetas_601.json"
    before = path.read_bytes()
    result = RecetaDocumentacionWriteService(
        tmp_path, generator=EmbeddedCriticalGenerator(),
    ).proposal(recipe_id=recipe_id, proposed={})

    assert result["datos_propuestos_ia"] == {"rendimiento": 4.0}
    assert {item["campo"] for item in result["propuestas_bloqueadas_revision"]} == {"descripcion", "observaciones", "elaboracion"}
    assert any("RENDIMIENTO_EMBEBIDO" in item["motivos"] for item in result["propuestas_bloqueadas_revision"])
    assert any("TEMPERATURA_SEGURIDAD_EMBEBIDA" in item["motivos"] for item in result["propuestas_bloqueadas_revision"])
    assert path.read_bytes() == before


def test_caso_salsa_con_tiempo_total_opcional_lo_solicita_y_explica_campos_manuales(tmp_path: Path) -> None:
    recipe_id = _recipe(tmp_path)
    repository = RepositorioBibliotecaRecetas601(tmp_path)
    repository.editar(recipe_id, {
        "elaboracion": "Pochar, reducir, añadir nata y triturar.",
        "tiempo_activo": "20 minutos", "vida_util_congelado": "1 mes",
        "regeneracion": "Calentar suavemente.",
    })
    calls = []

    class FakeGenerator:
        def generate(self, *, recipe, missing_fields, allowed_fields):
            calls.append({"recipe": recipe, "missing_fields": missing_fields, "allowed_fields": allowed_fields})
            return {"tiempo_total": "45 minutos", "elaboracion": "No debe sobrescribirse."}

    result = RecetaDocumentacionWriteService(tmp_path, repository=repository, generator=FakeGenerator()).proposal(recipe_id=recipe_id, proposed={})

    assert "Tiempo total" in calls[0]["missing_fields"]
    assert "Elaboración paso a paso" not in calls[0]["missing_fields"]
    assert result["datos_propuestos_ia"] == {"tiempo_total": "45 minutos", "rendimiento": 4.0}
    assert {"key": "elaboracion", "reason": "EXISTING_VALUE"} in result["campos_descartados"]
    assert result["campos_pendientes_no_proponibles"] == []
    assert repository.obtener(recipe_id)["tiempo_total"] == ""


def test_factory_http_reutiliza_engine_canonico_y_sustituye_solo_provider_externo(tmp_path: Path) -> None:
    recipe_id = _recipe(tmp_path)
    calls = []

    class FakeExternalProvider:
        provider_name = "OPENAI"
        model_name = "fake-external"
        connected = True
        supports_tool_calling = True

        def ejecutar(self, request):
            calls.append(request)
            return HostAIProviderResult(
                ok=True,
                proveedor=self.provider_name,
                modelo=self.model_name,
                salida={"mensaje": json.dumps({"elaboracion": "Propuesta nueva desde el provider externo."})},
                errores=[],
            )

    platform = HostAIPlatformAPI(base_dir=tmp_path)
    canonical_engine = platform.facade._get_core().orquestador.host_ai_engine
    canonical_engine._providers["OPENAI"] = FakeExternalProvider()
    canonical_engine.default_provider = "SIMULADO"

    client = TestClient(create_app(platform))
    response = client.post(
        f"/api/v1/biblioteca/elaboraciones/{recipe_id}/documentacion/propuesta",
        json={"proposed": {}},
    )
    payload = response.json()
    service = platform.facade._get_recipe_docs_service()

    assert response.status_code == 200
    assert calls and calls[0].proveedor_preferido == "OPENAI"
    prompt = str(calls[0].datos_enviados.get("pregunta") or "")
    assert "No insertes en descripcion" in prompt
    assert "No agregues ingredientes que no aparezcan" in prompt
    assert service.generator.engine is canonical_engine
    assert payload["datos_propuestos_ia"] == {
        "elaboracion": "Propuesta nueva desde el provider externo.", "rendimiento": 4.0,
    }
    assert payload["datos_reales_modificados"] is False
    preview = client.post(
        f"/api/v1/biblioteca/elaboraciones/{recipe_id}/documentacion/preview",
        json={"selected": payload["datos_propuestos_ia"], "overwrite_fields": []},
    )
    assert preview.status_code == 200 and preview.json()["requiere_confirmacion"] is True
    confirmed = client.post(
        f"/api/v1/biblioteca/elaboraciones/{recipe_id}/documentacion/confirmar",
        json={"selected": payload["datos_propuestos_ia"], "overwrite_fields": [], "preview_token": preview.json()["preview_token"]},
    )
    reread = RepositorioBibliotecaRecetas601(tmp_path).obtener(recipe_id)
    assert confirmed.status_code == 200 and confirmed.json()["lectura_posterior_verificada"] is True
    assert reread["elaboracion"] == "Propuesta nueva desde el provider externo."
    assert reread["procedencia_campos"]["elaboracion"]["tipo"] == "IA"


def test_endpoint_real_propone_tiempo_total_y_expone_pendientes_manuales(tmp_path: Path) -> None:
    recipe_id = _recipe(tmp_path)
    repository = RepositorioBibliotecaRecetas601(tmp_path)
    repository.editar(recipe_id, {
        "elaboracion": "Procedimiento existente.", "tiempo_activo": "20 minutos",
        "vida_util_congelado": "1 mes", "regeneracion": "Calentar suavemente.",
    })
    requests = []

    class FakeExternalProvider:
        provider_name = "OPENAI"
        model_name = "fake-external"
        connected = True
        supports_tool_calling = True

        def ejecutar(self, request):
            requests.append(request)
            return HostAIProviderResult(ok=True, proveedor="OPENAI", modelo="fake-external", salida={"mensaje": json.dumps({"tiempo_total": "45 minutos"})}, errores=[])

    platform = HostAIPlatformAPI(base_dir=tmp_path)
    engine = platform.facade._get_core().orquestador.host_ai_engine
    engine._providers["OPENAI"] = FakeExternalProvider()
    engine.default_provider = "SIMULADO"
    response = TestClient(create_app(platform)).post(
        f"/api/v1/biblioteca/elaboraciones/{recipe_id}/documentacion/propuesta", json={"proposed": {}},
    )

    payload = response.json()
    assert response.status_code == 200 and len(requests) == 1
    assert payload["datos_propuestos_ia"] == {"tiempo_total": "45 minutos", "rendimiento": 4.0}
    assert "Tiempo total" in payload["campos_pendientes_proponibles"]
    assert payload["campos_pendientes_no_proponibles"] == []
    assert repository.obtener(recipe_id)["tiempo_total"] == ""


def test_error_timeout_provider_es_trazable_y_no_es_falso_exito(tmp_path: Path, caplog) -> None:
    class ConnectedProvider:
        connected = True

    class TimeoutEngine:
        default_provider = "OPENAI"
        _providers = {"OPENAI": ConnectedProvider()}

        def ejecutar(self, request):
            return type("Response", (), {"estado": "ERROR", "errores": ["OpenAI no respondió dentro del tiempo permitido."], "request_id": "HAE-TIMEOUT", "proveedor": "OPENAI", "modelo": "gpt-5-mini"})()

    generator = HostAIRecipeProposalGenerator(tmp_path, engine=TimeoutEngine())
    with pytest.raises(RecetaDocumentacionError) as raised:
        generator.generate(recipe={"id": "REC-1", "nombre": "Salsa", "elaboracion": "Procedimiento existente"}, missing_fields=["Tiempo total"], allowed_fields={"elaboracion", "tiempo_total"})

    assert raised.value.code == "ai_provider_timeout"
    assert "recipe_ai_provider_failed" in caplog.text
    assert "HAE-TIMEOUT" in caplog.text and "category=timeout" in caplog.text


def test_filtro_registra_claves_sin_contenido_y_descarta_alias_no_canonicos(tmp_path: Path, caplog) -> None:
    class ConnectedProvider:
        connected = True

    class StructuredEngine:
        default_provider = "OPENAI"
        _providers = {"OPENAI": ConnectedProvider()}

        def ejecutar(self, request):
            return type("Response", (), {
                "estado": "OK", "errores": [], "request_id": "HAE-FILTER",
                "proveedor": "OPENAI", "modelo": "fake",
                "respuesta": {"mensaje": json.dumps({
                    "tiempo_total": "45 minutos", "duracion_total": "45", "tiempo_activo": "20 minutos",
                })},
            })()

    caplog.set_level("INFO")
    result = HostAIRecipeProposalGenerator(tmp_path, engine=StructuredEngine()).generate(
        recipe={"id": "REC-SALSA", "nombre": "Salsa", "tiempo_activo": "Ya guardado"},
        missing_fields=["Tiempo total"], allowed_fields={"tiempo_total", "tiempo_activo"},
    )

    assert result == {"tiempo_total": "45 minutos"}
    assert result.diagnostics["returned_keys"] == ["duracion_total", "tiempo_activo", "tiempo_total"]
    assert result.diagnostics["discarded_keys"] == [
        {"key": "duracion_total", "reason": "NOT_ALLOWED"},
        {"key": "tiempo_activo", "reason": "NOT_REQUESTED"},
    ]
    assert "recipe_ai_proposal_filter" in caplog.text
    assert "45 minutos" not in caplog.text
