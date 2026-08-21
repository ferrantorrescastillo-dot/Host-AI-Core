from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from SERVICIOS.host_ai_platform import (
    ActionContextError, ActionContextStore, AuthorizedExecutionContext,
    DuplicateToolError, OperationClass, PlatformPolicy, SessionContext,
    ToolDefinition, ToolExecutor, ToolRegistry, ToolResult, UIAction,
)


def context(*scopes: str) -> AuthorizedExecutionContext:
    return AuthorizedExecutionContext("req-fake", "user-fake", "tenant-fake", scopes=frozenset(scopes))


def definition(tool_id: str, operation: OperationClass, *scopes: str) -> ToolDefinition:
    return ToolDefinition(tool_id, "Fake tool", operation, {"type": "object"}, frozenset(scopes))


def test_registry_executor_and_operation_classes() -> None:
    registry = ToolRegistry()
    received = []

    def handler(params, execution_context):
        received.append((params, execution_context))
        return ToolResult("OK", "done", {"value": params.get("value")})

    registry.register(definition("fake-read", OperationClass.READ), handler)
    assert registry.has("fake-read")
    assert registry.capabilities()[0]["operation_class"] == "READ"
    result = ToolExecutor(registry).execute("fake-read", {"value": 3}, context())
    assert result.status == "OK" and result.data == {"value": 3}
    assert received[0][1].tenant_id == "tenant-fake"
    assert ToolExecutor(registry).execute("missing", {}, context()).error_code == "unknown_tool"
    with pytest.raises(DuplicateToolError):
        registry.register(definition("fake-read", OperationClass.READ), handler)

    for operation in (OperationClass.PURE_CALC, OperationClass.UI_ACTION):
        registry.register(definition(f"fake-{operation.value.lower()}", operation), handler)
        assert ToolExecutor(registry).execute(f"fake-{operation.value.lower()}", {}, context()).status == "OK"


@pytest.mark.parametrize("operation", (OperationClass.PREVIEW, OperationClass.CONFIRM))
def test_scoped_operations(operation: OperationClass) -> None:
    registry = ToolRegistry()
    registry.register(definition(f"fake-{operation.value.lower()}", operation, "fake:write"), lambda _p, _c: ToolResult("OK", "done"))
    executor = ToolExecutor(registry, PlatformPolicy())
    assert executor.execute(f"fake-{operation.value.lower()}", {}, context("fake:write")).status == "OK"
    assert executor.execute(f"fake-{operation.value.lower()}", {}, context()).error_code == "missing_required_scope"


def test_confirm_without_declared_scope_is_rejected() -> None:
    registry = ToolRegistry()
    registry.register(definition("fake-confirm", OperationClass.CONFIRM), lambda _p, _c: ToolResult("OK", "bad"))
    assert ToolExecutor(registry).execute("fake-confirm", {}, context()).error_code == "confirm_scope_required"


def test_ui_action_contract() -> None:
    assert UIAction("FAKE", "DETAIL", "fake-1", "Open").to_public_dict() == {
        "type": "OPEN_VIEW", "target": "FAKE", "id": "fake-1", "view": "DETAIL", "label": "Open",
    }


def test_session_domain_state_isolated_and_copied() -> None:
    a, b = SessionContext("session-A"), SessionContext("session-B")
    a.set_domain_state("fake-a", {"value": 1})
    a.set_domain_state("fake-b", {"value": 2})
    b.set_domain_state("fake-a", {"value": 9})
    leaked = a.get_domain_state("fake-a")
    leaked["value"] = 99
    assert a.get_domain_state("fake-a") == {"value": 1}
    assert a.get_domain_state("fake-b") == {"value": 2}
    assert b.get_domain_state("fake-a") == {"value": 9}


def test_action_context_security_and_public_shape() -> None:
    now = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    store = ActionContextStore(lambda: now[0])
    public = store.create("fake-action", "session-A", {"secret": 7}, 30, "v1")
    assert set(public) == {"action_id", "action_context_id"}
    assert len(public["action_context_id"]) == 32 and "secret" not in public
    cid = public["action_context_id"]
    assert store.resolve(cid, "fake-action", "session-A", "v1") == {"secret": 7}
    for args, code in (
        ((cid, "fake-action", "session-B", "v1"), "session_mismatch"),
        ((cid, "other", "session-A", "v1"), "action_id_mismatch"),
        ((cid, "fake-action", "session-A", "v2"), "stale_action_context"),
    ):
        with pytest.raises(ActionContextError) as exc:
            store.resolve(*args)
        assert exc.value.code == code
    assert store.consume(cid, "fake-action", "session-A", "v1") == {"secret": 7}
    with pytest.raises(ActionContextError) as replay:
        store.resolve(cid, "fake-action", "session-A", "v1")
    assert replay.value.code == "action_context_replayed"
    expiring = store.create("expire", "session-A", {}, 1)
    now[0] += timedelta(seconds=2)
    with pytest.raises(ActionContextError) as expired:
        store.resolve(expiring["action_context_id"], "expire", "session-A")
    assert expired.value.code == "action_context_expired"


def test_fake_extension_preview_confirm_and_state() -> None:
    registry, session = ToolRegistry(), SessionContext("session-fake")
    actions = ActionContextStore()

    def preview(params, _context):
        session.set_domain_state("fake", {"pending": params["value"]})
        public = actions.create("fake-confirm", session.session_id, {"value": params["value"]}, 30)
        return ToolResult("OK", "preview", public)

    def confirm(params, _context):
        payload = actions.consume(params["context_id"], "fake-confirm", session.session_id)
        session.set_domain_state("fake", {"confirmed": payload["value"]})
        return ToolResult("OK", "confirmed")

    registry.register(definition("fake-preview", OperationClass.PREVIEW, "fake:write"), preview)
    registry.register(definition("fake-confirm", OperationClass.CONFIRM, "fake:write"), confirm)
    executor = ToolExecutor(registry)
    first = executor.execute("fake-preview", {"value": 8}, context("fake:write"))
    second = executor.execute("fake-confirm", {"context_id": first.data["action_context_id"]}, context("fake:write"))
    assert second.status == "OK" and session.get_domain_state("fake") == {"confirmed": 8}


def test_platform_imports_are_domain_neutral() -> None:
    root = Path(__file__).resolve().parents[1] / "SERVICIOS" / "host_ai_platform"
    forbidden = {"reservas", "escandallos", "articulos", "compras", "produccion", "menus"}
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name.lower() for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(str(node.module or "").lower())
        assert not any(term in imported for imported in imports for term in forbidden), (path, imports)
