from __future__ import annotations

from typing import Any
import pytest
from SERVICIOS.host_ai_platform import AuthorizedExecutionContext, HostAIEconomyPort, SessionContext, ToolExecutor, ToolRegistry, register_economy_domain


class InMemoryEconomy:
    def __init__(self, recipe_id: str, article_id: str, incident: str = "CONVERSION_NO_DISPONIBLE") -> None:
        self.recipe_id, self.article_id, self.incident, self.fixed = recipe_id, article_id, incident, False
        self.previews: dict[str, dict[str, Any]] = {}

    def incomplete_cost(self, recipe_id: str) -> dict[str, Any]:
        assert recipe_id == self.recipe_id
        reasons = [] if self.fixed else [{"tipo": self.incident, "articulo_id": self.article_id}]
        return {"ok": True, "receta_id": recipe_id, "nombre": f"Recipe {recipe_id}", "consulta_economica": "DETAIL_COSTE_INCOMPLETO",
                "estado_coste": "DISPONIBLE" if self.fixed else "PARCIAL", "coste_completo": self.fixed, "motivos": reasons,
                "coste_total": 12.5 if self.fixed else None, "explicacion": "Coste comprobado."}

    def preview_article_change(self, operation: str, article_id: str, values: dict[str, Any], context: AuthorizedExecutionContext, session_id: str) -> dict[str, Any]:
        assert article_id == self.article_id and session_id == "session-a"
        token = f"preview-{operation.lower()}"; self.previews[token] = {"operation": operation, "values": values}
        return {"ok": True, "preview_token": token, "operacion": operation, "datos_reales_modificados": False}

    def confirm_article_change(self, preview_token: str, context: AuthorizedExecutionContext, session_id: str) -> dict[str, Any]:
        assert preview_token in self.previews and session_id == "session-a"; self.fixed = True
        return {"ok": True, "estado": "CONFIRMADO", "datos_reales_modificados": True}

    def physical_yield(self, recipe_id: str) -> dict[str, Any]:
        return {"ok": True, "receta_id": recipe_id, "rendimiento_fisico": 0.82, "explicacion": "Rendimiento fÃ­sico disponible."}


def setup_flow(recipe_id="recipe-any", article_id="article-any", incident="CONVERSION_NO_DISPONIBLE"):
    port, registry, session = InMemoryEconomy(recipe_id, article_id, incident), ToolRegistry(), SessionContext("session-a")
    domain = register_economy_domain(registry, port, session); executor = ToolExecutor(registry)
    context = AuthorizedExecutionContext("request-a", "user-a", "tenant-a", scopes=frozenset({"escandallos:read", "articulos:preview", "articulos:write"}))
    return port, registry, session, domain, executor, context


def test_complete_economic_roundtrip_is_generic_and_server_side() -> None:
    recipe_id, article_id = "REC-DYNAMIC-91", "ART-DYNAMIC-44"
    port, registry, session, domain, executor, context = setup_flow(recipe_id, article_id)
    initial = executor.execute("economy.incomplete_cost", {"recipe_id": recipe_id}, context)
    assert initial.data["estado_coste"] == "PARCIAL"
    incident_action = next(a for a in initial.data["actions"] if a["action_id"] == "RESOLVE_MISSING_CONVERSION")
    stored = domain.actions.resolve(incident_action["action_context_id"], "RESOLVE_MISSING_CONVERSION", session.session_id)
    assert (stored["recipe_id"], stored["article_id"]) == (recipe_id, article_id)
    preview = executor.execute("economy.preview_article_change", {"operation": "UPDATE_CONVERSION", "article_id": article_id,
                               "values": {"unidad_origen": "u", "unidad_destino": "kg", "factor": 0.2}}, context)
    public_action = preview.data["action"]
    assert preview.data["datos_reales_modificados"] is False and set(public_action) == {"action_id", "label", "action_context_id"}
    confirmed = executor.execute("economy.confirm_article_change", {"action_context_id": public_action["action_context_id"]}, context)
    checked = executor.execute("economy.check_costing", {"action_context_id": confirmed.data["action"]["action_context_id"]}, context)
    assert checked.data["coste_completo"] is True and checked.data["consulta_economica"] == "DETAIL_COSTE_INCOMPLETO"
    assert checked.context_updates["economy"]["economic_incidents"] == []
    assert executor.execute("economy.physical_yield", {}, context).data["rendimiento_fisico"] == 0.82
    opened = executor.execute("economy.open_costing", {}, context).data["action"]["ui_action"]
    assert opened == {"type": "OPEN_VIEW", "target": "BIBLIOTECA", "id": recipe_id, "view": "ESCANDALLO", "label": "Abrir escandallo"}


@pytest.mark.parametrize("operation,incident", [("UPDATE_PRICE", "PRECIO_NO_DISPONIBLE"), ("UPDATE_CONVERSION", "CONVERSION_NO_DISPONIBLE"), ("UPDATE_FORMAT", "FORMATO_NO_DISPONIBLE")])
def test_all_article_corrections_share_preview_and_confirmation(operation: str, incident: str) -> None:
    port, registry, session, domain, executor, context = setup_flow(incident=incident)
    assert any(a["action_id"].startswith("RESOLVE_MISSING_") for a in executor.execute("economy.incomplete_cost", {"recipe_id": port.recipe_id}, context).data["actions"])
    preview = executor.execute("economy.preview_article_change", {"operation": operation, "article_id": port.article_id, "values": {"value": 7}}, context)
    assert preview.data["operacion"] == operation
    assert executor.execute("economy.confirm_article_change", {"action_context_id": preview.data["action"]["action_context_id"]}, context).status == "OK"


def test_scopes_session_replay_and_domain_separation() -> None:
    port, registry, session, domain, executor, context = setup_flow()
    ids = {item.tool_id for item in registry.definitions()}
    assert ids and all(item.startswith("economy.") for item in ids)
    denied = AuthorizedExecutionContext("r", "u", "t", scopes=frozenset())
    assert executor.execute("economy.preview_article_change", {"operation": "UPDATE_PRICE", "article_id": port.article_id}, denied).error_code == "missing_required_scope"
    preview = executor.execute("economy.preview_article_change", {"operation": "UPDATE_PRICE", "article_id": port.article_id}, context).data["action"]
    other_registry = ToolRegistry(); register_economy_domain(other_registry, port, SessionContext("session-b"), domain.actions)
    assert ToolExecutor(other_registry).execute("economy.confirm_article_change", {"action_context_id": preview["action_context_id"]}, context).error_code == "session_mismatch"
    assert executor.execute("economy.confirm_article_change", {"action_context_id": preview["action_context_id"]}, context).status == "OK"
    assert executor.execute("economy.confirm_article_change", {"action_context_id": preview["action_context_id"]}, context).error_code == "action_context_replayed"


def test_extension_imports_no_other_business_domain() -> None:
    from pathlib import Path
    source = Path(__file__).parents[1] / "SERVICIOS" / "host_ai_platform" / "economy.py"
    imports = " ".join(line.lower() for line in source.read_text(encoding="utf-8").splitlines() if line.startswith(("from ", "import ")))
    assert not any(word in imports for word in ("reservas", "menus", "compras", "produccion"))


def test_canonical_adapter_delegates_without_reimplementing_economics() -> None:
    class Costings:
        def consultar(self, **kwargs):
            assert kwargs == {"agregacion": "DETAIL_COSTE_INCOMPLETO", "escandallo_id": "REC-X"}
            return {"ok": True, "motivos": []}
    class Changes:
        def preview_change(self, **kwargs):
            assert kwargs["operation"] == "UPDATE_FORMAT" and kwargs["article_id"] == "ART-X"
            assert "recipe_id" not in kwargs and "scopes" not in kwargs
            return {"ok": True, "preview_token": "token"}
        def confirm_change(self, **kwargs):
            assert kwargs["preview_token"] == "token"
            return {"ok": True}
    context = AuthorizedExecutionContext("r", "u", "t")
    adapter = HostAIEconomyPort(Costings(), Changes(), lambda recipe_id: {"ok": True, "receta_id": recipe_id})
    assert adapter.incomplete_cost("REC-X")["ok"]
    assert adapter.preview_article_change("UPDATE_FORMAT", "ART-X", {"unidad_compra": "caja", "recipe_id": "forbidden", "scopes": ["*"]}, context, "s")["preview_token"] == "token"
    assert adapter.confirm_article_change("token", context, "s")["ok"]
    assert adapter.physical_yield("REC-X")["receta_id"] == "REC-X"
