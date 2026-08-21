from __future__ import annotations

from datetime import datetime
from pathlib import Path

from SERVICIOS.host_ai_platform import (
    AuthorizedExecutionContext, HostAIReservationsPort, SessionContext,
    ToolExecutor, ToolRegistry, register_reservations_domain,
)
from SERVICIOS.reservas_read_service import ReservasReadService
from SERVICIOS.reservas_write_service import ReservasWriteService


def setup_runtime(base_dir: Path, session_id: str = "session-reservations"):
    reads = ReservasReadService(base_dir)
    writes = ReservasWriteService(base_dir, now_provider=lambda: datetime(2030, 5, 1, 10, 0, 0))
    registry, session = ToolRegistry(), SessionContext(session_id)
    domain = register_reservations_domain(registry, HostAIReservationsPort(reads, writes), session)
    executor = ToolExecutor(registry)
    context = AuthorizedExecutionContext("request-r", "maitre", "restaurant",
                                         scopes=frozenset({"reservas:read", "reservas:preview", "reservas:write"}))
    return registry, session, domain, executor, context


def execute_preview_and_confirm(executor, context, operation, payload=None, reservation_id=""):
    preview = executor.execute("reservations.preview", {
        "operation": operation, "reservation_id": reservation_id, "payload": payload or {},
    }, context)
    assert preview.status == "OK" and preview.data["datos_reales_modificados"] is False
    public = preview.data["action"]
    assert set(public) == {"action_id", "label", "action_context_id"}
    return executor.execute("reservations.confirm", {"action_context_id": public["action_context_id"]}, context)


def test_full_reservation_flow_uses_real_temporary_services(tmp_path: Path) -> None:
    registry, session, domain, executor, context = setup_runtime(tmp_path)
    created = execute_preview_and_confirm(executor, context, "CREAR", {
        "nombre_cliente": "Cliente dinÃ¡mico", "fecha": "2030-05-20", "hora": "21:00", "pax": 4,
        "servicio": "CENA", "observaciones": "Mesa tranquila", "evento_id": None,
    })
    assert created.status == "OK" and created.data["datos_reales_modificados"] is True
    reservation_id = created.data["reserva"]["reserva_id"]
    assert reservation_id and session.active_entity["id"] == reservation_id

    listed = executor.execute("reservations.list", {"fecha": "2030-05-20", "nombre": "dinÃ¡mico"}, context)
    assert [item["reserva_id"] for item in listed.data["reservas"]] == [reservation_id]
    assert "observaciones" not in listed.data["reservas"][0]
    detail = executor.execute("reservations.detail", {"reservation_id": reservation_id.lower()}, context)
    assert detail.data["reserva"]["observaciones"] == "Mesa tranquila"

    modified = execute_preview_and_confirm(executor, context, "MODIFICAR", {"pax": 6}, reservation_id)
    assert modified.data["reserva"]["pax"] == 6
    confirmed = execute_preview_and_confirm(executor, context, "CONFIRMAR", reservation_id=reservation_id)
    assert confirmed.data["reserva"]["estado"] == "CONFIRMADA"
    completed = execute_preview_and_confirm(executor, context, "COMPLETAR", reservation_id=reservation_id)
    assert completed.data["reserva"]["estado"] == "COMPLETADA"

    opened = executor.execute("reservations.open", {}, context)
    assert opened.data["action"]["ui_action"] == {
        "type": "OPEN_VIEW", "target": "RESERVAS", "id": reservation_id,
        "view": "DETAIL", "label": "Abrir reserva",
    }


def test_cancel_flow_and_invalid_terminal_transition_are_grounded(tmp_path: Path) -> None:
    registry, session, domain, executor, context = setup_runtime(tmp_path)
    created = execute_preview_and_confirm(executor, context, "CREAR", {
        "nombre_cliente": "Otra persona", "fecha": "2030-06-01", "hora": "14:00", "pax": 2,
        "servicio": "COMIDA", "evento_id": None,
    })
    reservation_id = created.data["reserva"]["reserva_id"]
    cancelled = execute_preview_and_confirm(executor, context, "CANCELAR", reservation_id=reservation_id)
    assert cancelled.data["reserva"]["estado"] == "CANCELADA"
    rejected = executor.execute("reservations.preview", {"operation": "MODIFICAR", "reservation_id": reservation_id,
                                                          "payload": {"pax": 8}}, context)
    assert rejected.status == "ERROR" and rejected.error_code == "terminal_state"


def test_scopes_session_replay_and_server_side_tokens(tmp_path: Path) -> None:
    registry, session, domain, executor, context = setup_runtime(tmp_path)
    denied = AuthorizedExecutionContext("r", "u", "t", scopes=frozenset())
    assert executor.execute("reservations.preview", {"operation": "CREAR", "payload": {}}, denied).error_code == "missing_required_scope"
    preview = executor.execute("reservations.preview", {"operation": "CREAR", "payload": {
        "nombre_cliente": "Segura", "fecha": "2030-07-01", "hora": "13:00", "pax": 3,
        "servicio": "COMIDA", "evento_id": None,
    }}, context).data["action"]
    other_registry, other_session = ToolRegistry(), SessionContext("other-session")
    port = domain.port
    register_reservations_domain(other_registry, port, other_session, domain.actions)
    foreign = ToolExecutor(other_registry).execute("reservations.confirm", {"action_context_id": preview["action_context_id"]}, context)
    assert foreign.error_code == "session_mismatch"
    assert executor.execute("reservations.confirm", {"action_context_id": preview["action_context_id"]}, context).status == "OK"
    assert executor.execute("reservations.confirm", {"action_context_id": preview["action_context_id"]}, context).error_code == "action_context_replayed"


def test_reservations_are_namespaced_and_import_no_other_domain() -> None:
    registry, session, domain, executor, context = setup_runtime(Path("unused-fixture"))
    ids = {definition.tool_id for definition in registry.definitions()}
    assert ids and all(tool_id.startswith("reservations.") for tool_id in ids)
    source = Path(__file__).parents[1] / "SERVICIOS" / "host_ai_platform" / "reservations.py"
    imports = " ".join(line.lower() for line in source.read_text(encoding="utf-8").splitlines()
                       if line.startswith(("from ", "import ")))
    assert not any(name in imports for name in ("economy", "menus", "compras", "produccion"))
    session.set_domain_state("economy", {"sentinel": True})
    session.set_domain_state("reservations", {"reservation_id": "RSV-ISOLATED"})
    assert session.get_domain_state("economy") == {"sentinel": True}
