from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from API.app import HostAIPlatformAPI
from API.http_server import create_app
from MODELOS.reserva import RESERVA_ID_PATTERN, Reserva
from SERVICIOS.repositorio_reservas import RepositorioReservas
from SERVICIOS.reservas_read_service import ReservasReadService


def reserva(**overrides) -> Reserva:
    data = {"nombre_cliente": "Cliente Prueba", "fecha": "2030-05-20", "hora": "13:30", "pax": 4,
            "estado": "CONFIRMADA", "servicio": "COMIDA", "observaciones": "Alergia indicada en privado",
            "evento_id": None, "origen": "TELEFONO"}
    data.update(overrides)
    return Reserva.crear(**data)


def service_with(tmp_path: Path, *items: Reserva, today=date(2030, 5, 20)) -> ReservasReadService:
    RepositorioReservas(tmp_path).guardar_todos(items)
    return ReservasReadService(tmp_path, today_provider=lambda: today)


def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(platform_api=HostAIPlatformAPI(base_dir=tmp_path)))


def test_modelo_valido_id_canonico_y_evento_nulo() -> None:
    item = reserva()
    assert RESERVA_ID_PATTERN.fullmatch(item.reserva_id)
    assert item.evento_id is None


@pytest.mark.parametrize(("field", "value"), [
    ("pax", 0), ("pax", -1), ("fecha", "20/05/2030"), ("hora", "25:00"),
    ("estado", "INVENTADA"), ("servicio", "MERIENDA"),
])
def test_modelo_rechaza_valores_invalidos(field: str, value) -> None:
    with pytest.raises(ValueError):
        reserva(**{field: value})


def test_ids_generados_son_unicos() -> None:
    assert len({reserva().reserva_id for _ in range(100)}) == 100


def test_repositorio_round_trip_determinista_y_duplicados(tmp_path: Path) -> None:
    repo = RepositorioReservas(tmp_path)
    first, second = reserva(fecha="2030-05-21"), reserva(fecha="2030-05-20")
    repo.guardar_todos([first, second])
    assert [item.reserva_id for item in repo.listar()] == [second.reserva_id, first.reserva_id]
    with pytest.raises(ValueError, match="duplicado"):
        repo.guardar_todos([first, first])


def test_listado_vacio_no_crea_persistencia(tmp_path: Path) -> None:
    service = ReservasReadService(tmp_path)
    assert service.listar() == []
    assert not service.repo.path.exists()


def test_listado_orden_filtros_busquedas_y_limite(tmp_path: Path) -> None:
    a = reserva(nombre_cliente="Álvaro", fecha="2030-05-21", hora="20:00", estado="PENDIENTE", servicio="CENA")
    b = reserva(nombre_cliente="Beatriz", fecha="2030-05-20", hora="14:00")
    c = reserva(nombre_cliente="Carlos", fecha="2030-05-20", hora="13:00")
    service = service_with(tmp_path, a, b, c)
    assert [x["reserva_id"] for x in service.listar()] == [c.reserva_id, b.reserva_id, a.reserva_id]
    assert service.buscar_por_id(a.reserva_id)["nombre_cliente"] == "Álvaro"
    assert service.buscar_por_nombre("alvaro")[0]["reserva_id"] == a.reserva_id
    assert len(service.listar(fecha="2030-05-20")) == 2
    assert service.listar(estado="PENDIENTE")[0]["reserva_id"] == a.reserva_id
    assert service.listar(servicio="CENA")[0]["reserva_id"] == a.reserva_id
    assert len(service.listar(limite=1)) == 1


def test_hoy_y_proximas(tmp_path: Path) -> None:
    old, today, future = reserva(fecha="2030-05-19"), reserva(fecha="2030-05-20"), reserva(fecha="2030-05-21")
    service = service_with(tmp_path, old, today, future)
    assert [x["reserva_id"] for x in service.hoy()] == [today.reserva_id]
    assert [x["reserva_id"] for x in service.proximas()] == [today.reserva_id, future.reserva_id]


def test_detalle_inexistente_y_dto_privado(tmp_path: Path) -> None:
    item = reserva()
    service = service_with(tmp_path, item)
    assert service.detalle("RES-000000000000") is None
    listed = service.listar()[0]
    assert not {"observaciones", "origen", "telefono", "email"} & set(listed)
    assert service.detalle(item.reserva_id)["observaciones"] == item.observaciones


def test_evento_id_nulo_valido_e_inexistente(tmp_path: Path) -> None:
    ReservasReadService(tmp_path, evento_existe=lambda _value: False).validar_evento(reserva())
    valid = reserva(evento_id="EVT-1")
    ReservasReadService(tmp_path, evento_existe=lambda value: value == "EVT-1").validar_evento(valid)
    with pytest.raises(ValueError, match="no existe"):
        ReservasReadService(tmp_path, evento_existe=lambda _value: False).validar_evento(valid)


def test_evento_id_se_valida_con_fuente_eventos_existente(tmp_path: Path) -> None:
    db = tmp_path / "DATOS" / "db"; db.mkdir(parents=True)
    (db / "eventos.json").write_text(json.dumps([{"id": "EVT-REAL"}]), encoding="utf-8")
    service = ReservasReadService(tmp_path)
    service.validar_evento(reserva(evento_id="EVT-REAL"))
    with pytest.raises(ValueError):
        service.validar_evento(reserva(evento_id="EVT-NO"))


def test_aislamiento_base_dir(tmp_path: Path) -> None:
    one, two = tmp_path / "one", tmp_path / "two"
    service_with(one, reserva(nombre_cliente="Uno")); service_with(two, reserva(nombre_cliente="Dos"))
    assert ReservasReadService(one).listar()[0]["nombre_cliente"] == "Uno"
    assert ReservasReadService(two).listar()[0]["nombre_cliente"] == "Dos"


def test_read_no_modifica_persistencia(tmp_path: Path) -> None:
    item = reserva(); service = service_with(tmp_path, item); before = service.repo.path.read_bytes()
    service.listar(); service.hoy(); service.proximas(); service.detalle(item.reserva_id)
    assert service.repo.path.read_bytes() == before


def test_api_listado_filtros_y_detalle(tmp_path: Path) -> None:
    item = reserva(); RepositorioReservas(tmp_path).guardar_todos([item]); api = client(tmp_path)
    response = api.get("/api/v1/reservas", params={"estado": "CONFIRMADA", "servicio": "COMIDA"})
    assert response.status_code == 200
    assert response.json()["reservas"]["items"][0]["reserva_id"] == item.reserva_id
    detail = api.get(f"/api/v1/reservas/{item.reserva_id}")
    assert detail.status_code == 200 and detail.json()["reserva"]["observaciones"] == item.observaciones
    assert response.json()["datos_reales_modificados"] is False


def test_api_hoy_proximas_busqueda_y_vacio(tmp_path: Path) -> None:
    item = reserva(nombre_cliente="Cliente API", fecha=date.today().isoformat())
    RepositorioReservas(tmp_path).guardar_todos([item]); api = client(tmp_path)
    assert api.get("/api/v1/reservas", params={"alcance": "hoy"}).json()["reservas"]["total"] == 1
    assert api.get("/api/v1/reservas", params={"alcance": "proximas", "q": "api"}).json()["reservas"]["total"] == 1
    assert api.get("/api/v1/reservas", params={"q": "nadie"}).json()["reservas"]["items"] == []


def test_api_inexistente_filtros_invalidos_y_sin_write(tmp_path: Path) -> None:
    api = client(tmp_path)
    missing = api.get("/api/v1/reservas/RES-000000000000")
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "reserva_not_found"
    assert api.get("/api/v1/reservas", params={"estado": "OTRO"}).status_code == 400
    assert api.post("/api/v1/reservas", json={}).status_code == 404
    assert api.put("/api/v1/reservas/RES-000000000000", json={}).status_code == 404
    assert api.patch("/api/v1/reservas/RES-000000000000", json={}).status_code == 404
    assert api.delete("/api/v1/reservas/RES-000000000000").status_code == 404
