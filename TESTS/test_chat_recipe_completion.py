from pathlib import Path
from types import SimpleNamespace

from SERVICIOS.chat_host_ai_shell_service import ServicioChatHostAIShell
from SERVICIOS.receta_completion_workflow import RecipeCompletionInvestigation
from SERVICIOS.host_ai_agent_models import AgentRunResult
from TESTS.test_recipe_completion_workflow import _recipe
from TESTS.test_confirmacion_relacion_ingrediente import _service as _relation_service


class _Workflow:
    def __init__(self):
        self.calls = []

    def investigate(self, recipe_id):
        self.calls.append(recipe_id)
        return RecipeCompletionInvestigation(
            recipe_id, "He revisado la receta. Falta el procedimiento y una relación de ingrediente.",
            {"RESUELTO": [], "FALTA": [{"campo": "procedimiento"}], "AMBIGUO": [], "NO_VERIFICABLE": []},
            "Propuesta de IA, no registrada: procedimiento.",
            [{"action_id": "PREVIEW_RECIPE_PROCEDURE", "recipe_id": recipe_id}], {"missing_prices": []},
        )


class _RecipeReads:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def consultar(self, consulta, **params):
        self.calls.append((consulta, params))
        return self.response


def _investigation(recipe_id="REC-X", missing=None):
    return RecipeCompletionInvestigation(
        recipe_id, "Revisión completada.",
        {"RESUELTO": [], "FALTA": [{"campo": value} for value in (missing or [])], "AMBIGUO": [], "NO_VERIFICABLE": []},
        "", [], {},
    )


def test_peticion_normal_por_nombre_muestra_receta_utilizable_sin_provider(tmp_path: Path) -> None:
    service = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=SimpleNamespace(base_dir=tmp_path)))
    reads = _RecipeReads({"estado": "OK", "elaboracion": {
        "id": "REC-X", "nombre": "Receta X", "rendimiento": 4, "unidad_rendimiento": "raciones",
        "ingredientes": [{"nombre_original": "Patata", "cantidad": 0.3, "unidad": "kg"}],
        "procedimiento": "Cocer, enfriar y mezclar.", "conservacion": "Refrigerada.",
    }})
    service.recipe_completion_workflow = SimpleNamespace(recipes=reads, investigate=lambda recipe_id: _investigation(recipe_id))

    response = service.enviar("Dame la receta de Receta X")

    assert reads.calls[0][1]["termino"] == "receta x"
    assert "# Receta X" in response["mensaje"]
    assert "Patata — 0.3 kg" in response["mensaje"]
    assert "Cocer, enfriar y mezclar." in response["mensaje"]
    assert response["datos"]["datos_reales_modificados"] is False


def test_receta_incompleta_muestra_existente_y_opciones(tmp_path: Path) -> None:
    service = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=SimpleNamespace(base_dir=tmp_path)))
    reads = _RecipeReads({"estado": "OK", "elaboracion": {
        "id": "REC-X", "nombre": "Receta X", "ingredientes": [{"nombre_original": "Patata", "cantidad": 1, "unidad": "kg"}],
        "procedimiento": None,
    }})
    service.recipe_completion_workflow = SimpleNamespace(
        recipes=reads, investigate=lambda recipe_id: _investigation(recipe_id, ["procedimiento", "tiempos"]),
    )

    response = service.enviar("¿Cómo se prepara la receta X?")

    assert "Patata — 1 kg" in response["mensaje"]
    assert "Falta el procedimiento" in response["mensaje"]
    assert "Completar la receta conmigo" in response["mensaje"]
    assert "Proponer una receta con IA" in response["mensaje"]


def test_receta_ambigua_y_no_encontrada_no_seleccionan(tmp_path: Path) -> None:
    service = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=SimpleNamespace(base_dir=tmp_path)))
    candidates = [{"id": "REC-1", "nombre": "Crema"}, {"id": "REC-2", "nombre": "Crema tostada"}]
    service.recipe_completion_workflow = SimpleNamespace(
        recipes=_RecipeReads({"estado": "AMBIGUO", "elaboraciones": candidates}), investigate=lambda _recipe_id: None,
    )
    ambiguous = service.enviar("Dame la receta de crema")
    service.recipe_completion_workflow.recipes.response = {"estado": "NO_ENCONTRADO"}
    missing = service.enviar("Busca la receta de inexistente")

    assert ambiguous["datos"]["estado"] == "AMBIGUO" and len(ambiguous["datos"]["candidatos"]) == 2
    assert service._session.receta_activa == {}
    assert all(option in missing["mensaje"] for option in (
        "Buscar en mi biblioteca", "Proponer una receta con IA", "Crear la receta conmigo",
        "Vincular una receta existente", "Dejarla pendiente",
    ))


def test_abrir_receta_resuelve_nombre_y_usa_id_canonico(tmp_path: Path) -> None:
    service = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=SimpleNamespace(base_dir=tmp_path)))
    service.recipe_completion_workflow = SimpleNamespace(
        recipes=_RecipeReads({"estado": "OK", "elaboracion": {"id": "REC-CANONICA", "nombre": "Salsa X", "ingredientes": []}}),
        investigate=lambda recipe_id: _investigation(recipe_id),
    )
    calls = []
    service.tool_executor = SimpleNamespace(execute_agent_read=lambda tool_id, arguments: (
        calls.append((tool_id, arguments)) or SimpleNamespace(datos={"ui_action": {
            "type": "OPEN_VIEW", "target": "ELABORACION", "id": arguments["elaboracion_id"], "view": "RECETA",
        }})
    ))

    response = service.enviar("Abre la receta de Salsa X")

    assert calls == [("abrir_elaboracion", {"elaboracion_id": "REC-CANONICA", "vista": "receta"})]
    assert response["datos"]["ui_actions"][0]["id"] == "REC-CANONICA"


def test_fallback_receta_no_intercepta_objetivos_operativos_superiores(tmp_path: Path) -> None:
    service = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=SimpleNamespace(base_dir=tmp_path)))
    reads = _RecipeReads({"estado": "NO_ENCONTRADO"})
    service.recipe_completion_workflow = SimpleNamespace(recipes=reads, investigate=lambda _recipe_id: None)
    for request in (
        "Analiza el menú X completo, revisa recetas, necesidades, stock y compras.",
        "Hazme la producción del evento X aunque falte una receta.",
        "Organiza el evento X y revisa sus recetas y compras.",
        "Analiza recetas, stock y compras de forma multifuente.",
    ):
        assert service._try_recipe_request(request) is None
    assert reads.calls == []


def test_objetivo_directo_de_receta_conserva_fallback(tmp_path: Path) -> None:
    service = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=SimpleNamespace(base_dir=tmp_path)))
    service.recipe_completion_workflow = SimpleNamespace(
        recipes=_RecipeReads({"estado": "NO_ENCONTRADO"}), investigate=lambda _recipe_id: None,
    )
    result = service._try_recipe_request("Dame una receta inexistente X")
    assert result is not None
    assert result["datos"]["estado"] == "NO_ENCONTRADO"
    assert "Proponer una receta con IA" in result["mensaje"]


def test_terminar_receta_investiga_automaticamente_y_conserva_workflow(tmp_path: Path) -> None:
    service = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=SimpleNamespace(base_dir=tmp_path)))
    workflow = _Workflow()
    service.recipe_completion_workflow = workflow
    service._session.receta_activa = {"id": "REC601-000001", "nombre": "Salsa"}
    service._session.contexto_activo = "ELABORACION"

    first = service.enviar("Termina esta receta.")
    second = service.enviar("¿Qué le falta?")

    assert workflow.calls == ["REC601-000001", "REC601-000001"]
    assert "Falta el procedimiento" in first["mensaje"]
    assert first["datos"]["recipe_completion"]["procedure_proposal"].startswith("Propuesta de IA")
    assert second["datos"]["workflow"]["workflow_type"] == "recipe_completion"
    assert first["datos"]["datos_reales_modificados"] is False


def test_procedimiento_requiere_preview_y_confirmacion_en_chat(tmp_path: Path) -> None:
    recipe_id = _recipe(tmp_path)
    service = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=SimpleNamespace(base_dir=tmp_path)))
    service.recipe_completion_workflow = _Workflow()
    service._session.receta_activa = {"id": recipe_id, "nombre": "Salsa"}
    service._session.contexto_activo = "ELABORACION"
    path = tmp_path / "DATOS" / "db" / "biblioteca_recetas_601.json"

    service.enviar("Termina esta receta.")
    before = path.read_bytes()
    preview = service.ejecutar_accion_reserva("PREVIEW_RECIPE_PROCEDURE")
    confirmed = service.ejecutar_accion_reserva("CONFIRM_RECIPE_PROCEDURE")

    assert preview["datos"]["datos_reales_modificados"] is False
    assert path.read_bytes() != before
    assert confirmed["datos"]["datos_reales_modificados"] is True


def test_relacion_ingrediente_desde_chat_usa_contexto_servidor_y_no_se_repite(tmp_path: Path) -> None:
    relation_service = _relation_service(tmp_path)
    first = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=SimpleNamespace(base_dir=tmp_path)), session_id="sesion-a")
    second = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=SimpleNamespace(base_dir=tmp_path)), session_id="sesion-b")
    first.ingredient_relation_service = relation_service
    second.ingredient_relation_service = relation_service
    first._session.confirmacion_relacion_ingrediente_pendiente = {
        "recipe_id": "REC-SALSA", "ingredient_index": 0, "article_id": "ART000238", "estado": "PROPUESTA_PENDIENTE",
    }

    preview = first.ejecutar_accion_reserva("PREVIEW_INGREDIENT_RELATION")
    denied_other_session = second.ejecutar_accion_reserva("CONFIRM_INGREDIENT_RELATION")
    confirmed = first.ejecutar_accion_reserva("CONFIRM_INGREDIENT_RELATION")
    replay = first.ejecutar_accion_reserva("CONFIRM_INGREDIENT_RELATION")

    assert preview["datos"]["datos_reales_modificados"] is False
    assert denied_other_session["datos"]["reason"] == "ingredient_relation_confirmation_missing"
    assert confirmed["datos"]["datos_reales_modificados"] is True
    assert replay["datos"]["reason"] == "ingredient_relation_confirmation_missing"
    assert relation_service.repository.listar()[0].receta.ingredientes[0].articulo_id == "ART000238"


def test_planificacion_compleja_prioriza_agente_modelo_si_hay_provider(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    provider = SimpleNamespace(connected=True, supports_tool_calling=True)
    engine = SimpleNamespace(default_provider="OPENAI", _providers={"OPENAI": provider})
    service = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=engine))
    service.general_agent.engine = engine
    service.agent_observability = SimpleNamespace(emit=lambda *_args, **_kwargs: None)
    service.general_agent.run = lambda *_args, **_kwargs: AgentRunResult(
        True, "Plan profesional generado por el modelo.", "HAA-1", "OPENAI", "frontier", 2,
        ["consultar_eventos", "consultar_produccion"],
    )

    response = service.enviar("Hazme la producción del próximo evento y organízamela profesionalmente.")

    assert response["mensaje"] == "Plan profesional generado por el modelo."
    assert response["datos"]["general_agent"]["final_answer_source"] == "MODEL"


def test_borrador_relevante_se_promueve_a_ui_action_segura(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOST_AI_GENERAL_AGENT_READ", "1")
    provider = SimpleNamespace(connected=True, supports_tool_calling=True)
    engine = SimpleNamespace(default_provider="OPENAI", _providers={"OPENAI": provider})
    service = ServicioChatHostAIShell(SimpleNamespace(host_ai_engine=engine))
    service.general_agent.engine = engine
    service.agent_observability = SimpleNamespace(emit=lambda *_args, **_kwargs: None)
    purchase_groups = [{
        "proveedor": "SARDA",
        "articulos": [{"articulo_id": "ART-AZUCAR", "nombre": "Azúcar", "cantidad": .1, "unidad": "kg"}],
        "estado_pedido": "borrador",
        "pedido_relacionado": {"pedido_id": "PED-0AD463508C", "estado": "borrador", "lineas_relevantes": []},
        "action": {"type": "OPEN_ORDER", "label": "Abrir borrador", "pedido_id": "PED-0AD463508C"},
    }]
    service.general_agent.run = lambda *_args, **_kwargs: AgentRunResult(
        True, "Compra necesaria.", "HAA-DRAFT", "OPENAI", "gpt-5-mini", 3,
        ["consultar_menu", "consultar_necesidades_operativas", "consultar_compras_pendientes"],
        ui_actions=[{"type": "OPEN_VIEW", "target": "COMPRA", "id": "", "view": "LISTADO", "label": "Compras"}],
        context_updates={"purchase_groups": purchase_groups, "operational_incidents": [{"articulo_id": "ART-AZUCAR", "reason": "FORMATO_PENDIENTE"}]},
    )

    response = service.enviar("Analiza el menú y la compra necesaria.")

    assert response["datos"]["ui_action"] == {
        "type": "OPEN_VIEW", "target": "COMPRA", "id": "PED-0AD463508C",
        "view": "PEDIDO", "label": "Abrir borrador", "safe": True,
        "datos_reales_modificados": False,
    }
    assert response["datos"]["purchase_groups"] == purchase_groups
    assert response["datos"]["operational_incidents"] == [{"articulo_id": "ART-AZUCAR", "reason": "FORMATO_PENDIENTE"}]
    assert response["datos"]["datos_reales_modificados"] is False
