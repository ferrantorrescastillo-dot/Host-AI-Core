from SERVICIOS.host_ai_conversation_brain import AIModelConfiguration, HostAIConversationBrain


def _brain() -> HostAIConversationBrain:
    return HostAIConversationBrain(AIModelConfiguration("fast", "standard", "frontier"))


def test_direct_question_uses_fast_route() -> None:
    route, workflow = _brain().prepare_turn("¿Cuánta patata tengo?")

    assert route.tier == "fast"
    assert route.model == "fast"
    assert workflow.workflow_type == ""


def test_recipe_completion_starts_persistent_workflow() -> None:
    route, workflow = _brain().prepare_turn("Ayúdame a completar esta receta.", active_entity={"id": "REC-1"})

    assert route.tier == "frontier"
    assert route.reason == "recipe_completion"
    assert workflow.workflow_type == "recipe_completion"
    assert workflow.active_entity == {"id": "REC-1"}
    assert "ingredientes" in workflow.pending


def test_hazme_produccion_es_workflow_complejo_frontier() -> None:
    route, workflow = _brain().prepare_turn("Hazme la producción del próximo evento y organízamela profesionalmente.")

    assert route.tier == "frontier"
    assert workflow.workflow_type == "production_planning"


def test_proponer_receta_con_ia_usa_frontier_y_recipe_completion() -> None:
    route, workflow = _brain().prepare_turn("Proponer una receta con IA para una crema de verduras")
    assert route.tier == "frontier"
    assert workflow.workflow_type == "recipe_completion"


def test_deeper_review_escalates_existing_workflow() -> None:
    state = {"workflow_type": "recipe_completion", "objective": "Completar receta", "checked": ["consultar_escandallos"]}
    route, workflow = _brain().prepare_turn("No me convence, piénsalo mejor.", state)

    assert route.tier == "frontier"
    assert route.reason == "user_requested_deeper_review"
    assert workflow.workflow_type == "recipe_completion"
    assert workflow.checked == ["consultar_escandallos"]


def test_completed_tools_remain_in_workflow_memory() -> None:
    state = {"workflow_type": "production_planning", "checked": ["consultar_eventos"]}

    result = _brain().record_tool_results(state, ["consultar_eventos", "consultar_produccion"])

    assert result.checked == ["consultar_eventos", "consultar_produccion"]
