from datetime import datetime, timedelta
import json

import pytest
from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from MODELOS.reserva import Reserva
from SERVICIOS.host_ai_authorized_execution_context import AuthorizedExecutionContext
from SERVICIOS.repositorio_reservas import RepositorioReservas
from SERVICIOS.reservas_read_service import ReservasReadService
from SERVICIOS.reservas_write_service import ErrorReservasWrite, ReservasWriteService


BASE = {"nombre_cliente": "Marta", "fecha": "2030-05-20", "hora": "21:00", "pax": 4, "servicio": "CENA", "observaciones": "Alergia privada"}


def context(request="REQ-1", user="chef", tenant="restaurante"):
    return AuthorizedExecutionContext(request, user, tenant, ("operador",), frozenset({"reservas:write"}))


def seed(path, estado="PENDIENTE"):
    item = Reserva(reserva_id="RES-AAAAAAAAAAAA", estado=estado, **BASE)
    RepositorioReservas(path).guardar_todos([item])
    return item


def test_preview_crear_no_persiste_confirmacion_e_idempotencia(tmp_path):
    service = ReservasWriteService(tmp_path)
    preview = service.preview(operacion="CREAR", payload=BASE, context=context(), session_id="s1")
    assert preview["propuesto"]["estado"] == "PENDIENTE"
    assert preview["datos_reales_modificados"] is False
    assert ReservasReadService(tmp_path).listar() == []
    result = service.confirm(preview_token=preview["preview_token"], context=context(), session_id="s1")
    assert result["reserva"]["reserva_id"].startswith("RES-")
    assert result["datos_reales_modificados"] is True
    replay = service.confirm(preview_token=preview["preview_token"], context=context(), session_id="s1")
    assert replay["idempotente"] is True
    assert len(ReservasReadService(tmp_path).listar()) == 1


@pytest.mark.parametrize(("field", "value"), [("pax", 0), ("fecha", "mañana"), ("hora", "25:00"), ("servicio", "MERIENDA")])
def test_crear_rechaza_datos_invalidos(tmp_path, field, value):
    with pytest.raises(ErrorReservasWrite) as error:
        ReservasWriteService(tmp_path).preview(operacion="CREAR", payload={**BASE, field: value}, context=context())
    assert error.value.code == "invalid_reserva"


def test_evento_invalido_y_campos_pii_extra_rechazados(tmp_path):
    service = ReservasWriteService(tmp_path)
    with pytest.raises(ErrorReservasWrite, match="evento_id"):
        service.preview(operacion="CREAR", payload={**BASE, "evento_id": "EVT-INEXISTENTE"}, context=context())
    with pytest.raises(ErrorReservasWrite) as error:
        service.preview(operacion="CREAR", payload={**BASE, "telefono": "123"}, context=context())
    assert error.value.code == "unknown_fields"


def test_token_invalido_expirado_y_otra_sesion(tmp_path):
    now = [datetime(2030, 1, 1, 10, 0)]
    service = ReservasWriteService(tmp_path, now_provider=lambda: now[0], ttl_seconds=30)
    preview = service.preview(operacion="CREAR", payload=BASE, context=context(), session_id="s1")
    with pytest.raises(ErrorReservasWrite) as invalid:
        service.confirm(preview_token="otro", context=context(), session_id="s1")
    assert invalid.value.code == "invalid_preview"
    with pytest.raises(ErrorReservasWrite) as foreign:
        service.confirm(preview_token=preview["preview_token"], context=context(), session_id="s2")
    assert foreign.value.code == "invalid_preview"
    now[0] += timedelta(seconds=31)
    with pytest.raises(ErrorReservasWrite) as expired:
        service.confirm(preview_token=preview["preview_token"], context=context(), session_id="s1")
    assert expired.value.code == "expired_preview"


def test_editar_confirmar_inmutables_y_concurrencia_stale(tmp_path):
    seed(tmp_path)
    service = ReservasWriteService(tmp_path)
    preview = service.preview(operacion="MODIFICAR", reserva_id="RES-AAAAAAAAAAAA", payload={"pax": 6}, context=context())
    assert service.read.detalle("RES-AAAAAAAAAAAA")["pax"] == 4
    result = service.confirm(preview_token=preview["preview_token"], context=context())
    assert result["reserva"]["pax"] == 6
    for payload in ({"reserva_id": "RES-BBBBBBBBBBBB"}, {"creado_en": "2030-01-01"}, {"estado": "CANCELADA"}):
        with pytest.raises(ErrorReservasWrite) as immutable:
            service.preview(operacion="MODIFICAR", reserva_id="RES-AAAAAAAAAAAA", payload=payload, context=context())
        assert immutable.value.code == "immutable_or_unknown_fields"
    stale = service.preview(operacion="MODIFICAR", reserva_id="RES-AAAAAAAAAAAA", payload={"pax": 8}, context=context())
    current = service.repo.obtener("RES-AAAAAAAAAAAA")
    service.repo.guardar_todos([Reserva.from_dict({**current.to_dict(), "pax": 7})])
    with pytest.raises(ErrorReservasWrite) as error:
        service.confirm(preview_token=stale["preview_token"], context=context())
    assert error.value.code == "stale_preview"


@pytest.mark.parametrize(("initial", "operation", "target"), [
    ("PENDIENTE", "CONFIRMAR", "CONFIRMADA"), ("PENDIENTE", "CANCELAR", "CANCELADA"),
    ("CONFIRMADA", "CANCELAR", "CANCELADA"), ("CONFIRMADA", "NO_SHOW", "NO_SHOW"),
    ("CONFIRMADA", "COMPLETAR", "COMPLETADA"),
])
def test_transiciones_validas_no_borran(tmp_path, initial, operation, target):
    seed(tmp_path, initial)
    service = ReservasWriteService(tmp_path)
    preview = service.preview(operacion=operation, reserva_id="RES-AAAAAAAAAAAA", payload={}, context=context())
    result = service.confirm(preview_token=preview["preview_token"], context=context())
    assert result["reserva"]["estado"] == target
    assert len(service.repo.listar()) == 1


def test_transicion_invalida_y_auditoria_sin_pii(tmp_path):
    seed(tmp_path, "CANCELADA")
    service = ReservasWriteService(tmp_path)
    with pytest.raises(ErrorReservasWrite) as error:
        service.preview(operacion="CONFIRMAR", reserva_id="RES-AAAAAAAAAAAA", payload={}, context=context())
    assert error.value.code == "terminal_state"
    RepositorioReservas(tmp_path).guardar_todos([])
    preview = service.preview(operacion="CREAR", payload=BASE, context=context("REQ-AUDIT"))
    service.confirm(preview_token=preview["preview_token"], context=context("REQ-AUDIT"))
    raw = service.audit_path.read_text(encoding="utf-8")
    event = json.loads(raw.splitlines()[-1])
    assert event["request_id"] == "REQ-AUDIT" and event["payload_hash"]
    assert "Marta" not in raw and "Alergia privada" not in raw


def test_pendiente_no_puede_completarse_y_no_genera_preview(tmp_path):
    seed(tmp_path, "PENDIENTE")
    service = ReservasWriteService(tmp_path)
    before = service.repo.path.read_bytes()
    with pytest.raises(ErrorReservasWrite) as error:
        service.preview(operacion="COMPLETAR", reserva_id="RES-AAAAAAAAAAAA", payload={}, context=context())
    assert error.value.code == "invalid_transition"
    assert service._pending == {}
    assert service.repo.path.read_bytes() == before


@pytest.mark.parametrize(("state", "operation", "payload"), [
    ("CANCELADA", "CONFIRMAR", {}),
    ("CANCELADA", "CANCELAR", {}),
    ("CANCELADA", "NO_SHOW", {}),
    ("CANCELADA", "COMPLETAR", {}),
    ("NO_SHOW", "CANCELAR", {}),
    ("NO_SHOW", "COMPLETAR", {}),
    ("COMPLETADA", "CANCELAR", {}),
    ("COMPLETADA", "COMPLETAR", {}),
])
def test_estado_terminal_rechaza_antes_de_preview_sin_persistir(tmp_path, state, operation, payload):
    seed(tmp_path, state)
    service = ReservasWriteService(tmp_path)
    before = service.repo.path.read_bytes()
    with pytest.raises(ErrorReservasWrite) as error:
        service.preview(operacion=operation, reserva_id="RES-AAAAAAAAAAAA", payload=payload, context=context(), session_id="terminal")
    assert error.value.code == "terminal_state"
    assert service._pending == {}
    assert service.repo.path.read_bytes() == before


@pytest.mark.parametrize("state", ["PENDIENTE", "CONFIRMADA", "CANCELADA", "NO_SHOW", "COMPLETADA"])
def test_cualquier_estado_admite_modificar_sin_cambiar_estado_y_eliminar_logicamente(tmp_path, state):
    seed(tmp_path, state)
    service = ReservasWriteService(tmp_path)
    edit = service.preview(operacion="MODIFICAR", reserva_id="RES-AAAAAAAAAAAA", payload={"observaciones": "Actualizada"}, context=context(), session_id="edit")
    assert edit["propuesto"]["estado"] == state
    edited = service.confirm(preview_token=edit["preview_token"], context=context(), session_id="edit")
    assert edited["reserva"]["estado"] == state
    deletion = service.preview(operacion="ELIMINAR", reserva_id="RES-AAAAAAAAAAAA", payload={}, context=context(), session_id="delete")
    assert deletion["datos_reales_modificados"] is False
    deleted = service.confirm(preview_token=deletion["preview_token"], context=context(), session_id="delete")
    repeated = service.confirm(preview_token=deletion["preview_token"], context=context(), session_id="delete")
    assert deleted["reserva"]["eliminada"] is True
    assert repeated["idempotente"] is True
    assert ReservasReadService(tmp_path).listar() == []
    assert service.repo.obtener("RES-AAAAAAAAAAAA") is not None


def test_aislamiento_read_y_api_exigen_preview_confirmacion(tmp_path, monkeypatch):
    monkeypatch.setenv("HOST_AI_INTERNAL_USER_ID", "web")
    monkeypatch.setenv("HOST_AI_INTERNAL_TENANT_ID", "restaurante")
    monkeypatch.setenv("HOST_AI_INTERNAL_SCOPES", "reservas:preview reservas:write")
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))
    body = {"operacion": "CREAR", "payload": BASE, "session_id": "web-session"}
    preview = client.post("/api/v1/reservas/preview", json=body, headers={"X-Request-ID": "REQ-PRE"})
    assert preview.status_code == 200 and preview.json()["datos_reales_modificados"] is False
    assert ReservasReadService(tmp_path).listar() == []
    changed = client.post("/api/v1/reservas/confirmar", json={"preview_token": preview.json()["preview_token"], "session_id": "web-session"}, headers={"X-Request-ID": "REQ-CONF"})
    assert changed.status_code == 200 and changed.json()["datos_reales_modificados"] is True
    direct = client.post("/api/v1/reservas", json=BASE)
    assert direct.status_code == 404
    other = tmp_path / "other"
    assert ReservasReadService(other).listar() == []


def test_api_reservas_preview_y_confirmacion_separan_scopes(tmp_path, monkeypatch):
    monkeypatch.setenv("HOST_AI_INTERNAL_USER_ID", "web")
    monkeypatch.setenv("HOST_AI_INTERNAL_TENANT_ID", "restaurante")
    monkeypatch.setenv("HOST_AI_INTERNAL_SCOPES", "reservas:preview")
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))
    body = {"operacion": "CREAR", "payload": BASE, "session_id": "ui-a"}
    preview = client.post("/api/v1/reservas/preview", json=body)
    assert preview.status_code == 200
    denied = client.post("/api/v1/reservas/confirmar", json={"preview_token": preview.json()["preview_token"], "session_id": "ui-a"})
    assert denied.status_code == 403
    assert ReservasReadService(tmp_path).listar() == []


def test_api_reservas_configuracion_interna_incompleta_sigue_denegada(tmp_path, monkeypatch):
    monkeypatch.delenv("HOST_AI_INTERNAL_USER_ID", raising=False)
    monkeypatch.setenv("HOST_AI_INTERNAL_TENANT_ID", "restaurante")
    monkeypatch.setenv("HOST_AI_INTERNAL_SCOPES", "reservas:preview")
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))
    denied = client.post("/api/v1/reservas/preview", json={"operacion": "CREAR", "payload": BASE, "session_id": "ui"})
    assert denied.status_code == 403
    assert ReservasReadService(tmp_path).listar() == []


def test_api_reservas_default_local_no_expone_contexto_y_aisla_sesion(tmp_path, monkeypatch):
    for name in ("HOST_AI_INTERNAL_USER_ID", "HOST_AI_INTERNAL_TENANT_ID", "HOST_AI_INTERNAL_SCOPES"):
        monkeypatch.delenv(name, raising=False)
    client = TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))
    preview = client.post("/api/v1/reservas/preview", json={"operacion": "CREAR", "payload": BASE, "session_id": "ui-a"})
    assert preview.status_code == 200
    assert not ({"user_id", "tenant_id", "scopes"} & set(preview.json()))
    foreign = client.post("/api/v1/reservas/confirmar", json={"preview_token": preview.json()["preview_token"], "session_id": "ui-b"})
    assert foreign.status_code == 409
    hostile = client.post("/api/v1/reservas/confirmar", json={"preview_token": "hostile", "session_id": "ui-a"})
    assert hostile.status_code == 409
    assert ReservasReadService(tmp_path).listar() == []
