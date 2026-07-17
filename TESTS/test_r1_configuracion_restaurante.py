from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from SERVICIOS.configuracion_restaurante import ServicioConfiguracionRestaurante
from SERVICIOS.produccion_guiada_piloto_13 import ProduccionGuiadaPiloto13


class _PlanFake:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._data


class _MotorFake:
    def __init__(self):
        self.plan = {
            "id": "P1",
            "nombre": "Servicio prueba",
            "fecha": "2026-07-17",
            "estado": "en_produccion",
            "tareas": [{"id": "T1"}],
        }
        self.tareas = [
            {
                "id": "T1",
                "titulo": "Tarea demo",
                "estado_ejecucion": "pendiente",
                "prioridad": 50,
                "tiempo_real_min": 0,
                "tiempo_restante_estimado_min": 10,
                "fases": [],
                "bloqueo": "",
                "checklist_pendiente": 0,
            }
        ]

    def listar_planes(self):
        return [self.plan]

    def obtener_plan(self, _plan_id):
        return _PlanFake(self.plan)

    def resumen_ejecucion(self, _plan_id):
        return {
            "plan": "Servicio prueba",
            "estado_plan": "en_produccion",
            "porcentaje_completado": 0,
            "total_tareas": 1,
            "tareas": self.tareas,
            "alertas": [],
            "tareas_pendientes": self.tareas,
        }

    def panel_produccion(self, _plan_id):
        return {
            "clasificacion_jornada": {"resumen": {}, "detalle": []},
            "cuellos_botella_previstos": {"resumen": {}, "detalle": []},
            "cronologia_operativa_prevista": {"resumen": {}, "base_horaria": {}, "alertas": [], "tramos": []},
        }

    def siguiente_tarea_recomendada(self, _plan_id):
        return {"codigo": "SUGERIDA", "tarea_id": "T1", "criterios": ["inicio natural"]}


def test_01_creacion_automatica(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    ruta = tmp_path / "DATOS" / "db" / "restaurante.json"
    assert not ruta.exists()
    config = servicio.obtener_configuracion()
    assert ruta.exists()
    assert config["version"] == "R1"


def test_02_lectura_escritura_y_persistencia(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    config = servicio.obtener_configuracion()
    config["datos_generales"]["nombre_restaurante"] = "Host AI Cocina"
    config["datos_generales"]["telefono"] = "+34 900 100 200"
    servicio.guardar_configuracion(config)

    servicio_2 = ServicioConfiguracionRestaurante(tmp_path)
    leida = servicio_2.obtener_configuracion()
    assert leida["datos_generales"]["nombre_restaurante"] == "Host AI Cocina"
    assert leida["datos_generales"]["telefono"] == "+34 900 100 200"


def test_03_modificacion_servicios(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    config = servicio.obtener_configuracion()
    config["servicios"].append(
        {
            "id": "servicio_brunch",
            "nombre": "Brunch",
            "hora_inicio": "10:30",
            "hora_fin": "12:30",
            "activo": True,
        }
    )
    servicio.guardar_configuracion(config)
    datos = servicio.obtener_configuracion()
    assert any(s["id"] == "servicio_brunch" for s in datos["servicios"])


def test_04_modificacion_partidas(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    config = servicio.obtener_configuracion()
    config["partidas"].append(
        {
            "id": "partida_panaderia",
            "nombre": "Panaderia",
            "orden": 4,
            "activa": True,
        }
    )
    servicio.guardar_configuracion(config)
    datos = servicio.obtener_configuracion()
    assert any(p["id"] == "partida_panaderia" for p in datos["partidas"])


def test_05_modificacion_equipamiento(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    config = servicio.obtener_configuracion()
    config["equipamiento"].append(
        {
            "id": "eq_roner",
            "nombre": "Roner",
            "tipo": "coccion_baja_temperatura",
            "activo": True,
        }
    )
    servicio.guardar_configuracion(config)
    datos = servicio.obtener_configuracion()
    assert any(e["id"] == "eq_roner" for e in datos["equipamiento"])


def test_06_modificacion_almacenes(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    config = servicio.obtener_configuracion()
    config["almacenes"].append(
        {
            "id": "almacen_secundario",
            "nombre": "Secundario",
            "activo": False,
        }
    )
    servicio.guardar_configuracion(config)
    datos = servicio.obtener_configuracion()
    assert any(a["id"] == "almacen_secundario" for a in datos["almacenes"])


def test_07_validacion_estructura(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    invalida = {
        "version": "R1",
        "datos_generales": {},
        "servicios": "mal",
        "partidas": [],
        "equipamiento": [],
        "almacenes": [],
    }
    resultado = servicio.validar_estructura(invalida)
    assert resultado["ok"] is False
    assert resultado["errores"]


def test_08_solo_configuracion_estructural(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    config = servicio.obtener_configuracion()
    prohibidos = {"stock", "produccion", "compras", "usuarios", "pedidos", "planificacion"}
    assert not (prohibidos & set(config.keys()))


def test_09_compatibilidad_con_produccion_guiada(tmp_path: Path):
    core = SimpleNamespace(base_dir=tmp_path, produccion_real=_MotorFake())
    servicio_guiada = ProduccionGuiadaPiloto13(core)
    panel = servicio_guiada.construir_panel("P1")
    assert panel["plan_id"] == "P1"
    assert (tmp_path / "DATOS" / "db" / "restaurante.json").exists()
    assert servicio_guiada.listar_planes_operativos()


def test_10_rechaza_duplicado_exacto_servicio(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    config = servicio.obtener_configuracion()
    config["servicios"].append(
        {
            "nombre": "Desayuno",
            "hora_inicio": "08:00",
            "hora_fin": "10:00",
            "activo": True,
        }
    )
    try:
        servicio.guardar_configuracion(config)
        assert False, "Debio rechazar servicio duplicado"
    except ValueError as exc:
        assert "Nombre duplicado en servicios" in str(exc)


def test_11_rechaza_duplicado_mayusculas_servicio(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    config = servicio.obtener_configuracion()
    config["servicios"].append(
        {
            "nombre": "dEsAyUnO",
            "hora_inicio": "08:00",
            "hora_fin": "10:00",
            "activo": True,
        }
    )
    try:
        servicio.guardar_configuracion(config)
        assert False, "Debio rechazar servicio duplicado por mayusculas"
    except ValueError as exc:
        assert "Nombre duplicado en servicios" in str(exc)


def test_12_rechaza_duplicado_espacios_servicio(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    config = servicio.obtener_configuracion()
    config["servicios"].append(
        {
            "nombre": "  Desayuno  ",
            "hora_inicio": "08:00",
            "hora_fin": "10:00",
            "activo": True,
        }
    )
    try:
        servicio.guardar_configuracion(config)
        assert False, "Debio rechazar servicio duplicado por espacios"
    except ValueError as exc:
        assert "Nombre duplicado en servicios" in str(exc)


def test_13_rechaza_duplicado_partida(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    config = servicio.obtener_configuracion()
    config["partidas"].append(
        {
            "nombre": " FrIo ",
            "orden": 10,
            "activa": True,
        }
    )
    try:
        servicio.guardar_configuracion(config)
        assert False, "Debio rechazar partida duplicada"
    except ValueError as exc:
        assert "Nombre duplicado en partidas" in str(exc)


def test_14_rechaza_duplicado_equipamiento(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    config = servicio.obtener_configuracion()
    config["equipamiento"].append(
        {
            "nombre": "horno rational",
            "tipo": "coccion",
            "activo": True,
        }
    )
    try:
        servicio.guardar_configuracion(config)
        assert False, "Debio rechazar equipamiento duplicado"
    except ValueError as exc:
        assert "Nombre duplicado en equipamiento" in str(exc)


def test_15_generacion_automatica_id_estable(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    config = servicio.obtener_configuracion()
    config["servicios"].append(
        {
            "nombre": "Brunch tarde",
            "hora_inicio": "11:00",
            "hora_fin": "13:00",
            "activo": True,
        }
    )
    config["equipamiento"].append(
        {
            "nombre": "Horno Rational XL",
            "tipo": "coccion",
            "activo": True,
        }
    )
    guardada = servicio.guardar_configuracion(config)
    servicio_brunch = next(s for s in guardada["servicios"] if s["nombre"] == "Brunch tarde")
    eq_xl = next(e for e in guardada["equipamiento"] if e["nombre"] == "Horno Rational XL")
    assert servicio_brunch["id"] == "servicio_brunch_tarde"
    assert eq_xl["id"] == "eq_horno_rational_xl"


def test_16_rechaza_id_duplicado_manual(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    config = servicio.obtener_configuracion()
    config["almacenes"].append(
        {
            "id": "almacen_principal",
            "nombre": "Almacen seco",
            "activo": True,
        }
    )
    try:
        servicio.guardar_configuracion(config)
        assert False, "Debio rechazar id duplicado"
    except ValueError as exc:
        assert "ID duplicado en almacenes" in str(exc)


def test_17_rechaza_orden_duplicado_partidas(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    config = servicio.obtener_configuracion()
    config["partidas"].append(
        {
            "nombre": "Panaderia",
            "orden": 1,
            "activa": True,
        }
    )
    try:
        servicio.guardar_configuracion(config)
        assert False, "Debio rechazar orden duplicado"
    except ValueError as exc:
        assert "Orden duplicado en partidas" in str(exc)


def test_18_persistencia_tras_rechazo(tmp_path: Path):
    servicio = ServicioConfiguracionRestaurante(tmp_path)
    original = servicio.obtener_configuracion()
    ruta = tmp_path / "DATOS" / "db" / "restaurante.json"
    antes = json.loads(ruta.read_text(encoding="utf-8"))

    mod = servicio.obtener_configuracion()
    mod["servicios"].append(
        {
            "nombre": "Comida",
            "hora_inicio": "13:00",
            "hora_fin": "15:00",
            "activo": False,
        }
    )
    try:
        servicio.guardar_configuracion(mod)
        assert False, "Debio rechazar duplicado"
    except ValueError:
        pass

    despues = json.loads(ruta.read_text(encoding="utf-8"))
    assert despues == antes
    assert original["servicios"] == servicio.obtener_configuracion()["servicios"]
