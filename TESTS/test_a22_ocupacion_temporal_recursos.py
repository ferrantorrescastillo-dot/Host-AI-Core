from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore


def _preparar_config(base: Path, recursos: dict[str, int] | None = None) -> None:
    cfg = base / "DATOS" / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    payload = {"recursos": recursos or {"horno": 1, "fogones": 4, "mesa_trabajo": 2, "abatidor": 1}}
    (cfg / "recursos_cocina_556e2.json").write_text(json.dumps(payload), encoding="utf-8")


def _buscar(lista: list[dict], clave: str, valor: str) -> dict:
    return next(item for item in lista if item.get(clave) == valor)


def _ocupados_en(ocupacion: dict, minuto: int, dia: int = 1) -> list[dict]:
    return [
        bloque for bloque in ocupacion.get("bloques", [])
        if int(bloque.get("dia", 1)) == int(dia) and int(bloque.get("inicio_min", 0)) <= minuto < int(bloque.get("fin_min", 0))
    ]


def test_recurso_libre_y_ocupado_con_calculo_interno(tmp_path):
    _preparar_config(tmp_path, {"horno": 1})
    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Ocupación base")
    tarea = core.produccion_real.anadir_tarea_manual(plan["id"], "Carrillera", prioridad=90)
    core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Hornear", 60, tipo="produccion", recurso="horno", responsable="cocinero")
    core.produccion_real.obtener_plan(plan["id"]).configuracion_planificacion = {"hora_inicio": "09:00"}
    core.produccion_real._persistir()

    ocupacion = core.produccion_real.ocupacion_temporal_recursos(plan["id"])

    assert ocupacion["resumen"]["total_bloques"] == 1
    assert ocupacion["resumen"]["bloques_calculo_interno"] == 1
    assert _ocupados_en(ocupacion, 8 * 60 + 55) == []
    ocupados = _ocupados_en(ocupacion, 9 * 60 + 30)
    assert len(ocupados) == 1
    assert ocupados[0]["recurso"] == "horno"
    assert ocupados[0]["fase"] == "Hornear"
    assert ocupados[0]["origen_dato"] == "calculo_interno"


def test_varios_bloques_consecutivos_y_varios_recursos(tmp_path):
    _preparar_config(tmp_path, {"fogones": 4, "mesa_trabajo": 2})
    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Secuencia")
    tarea = core.produccion_real.anadir_tarea_manual(plan["id"], "Demi-glace", prioridad=80)
    core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Preparar base", 20, tipo="preparacion", recurso="mesa_trabajo", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Reducir", 30, tipo="coccion", recurso="fuego", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Reducir más", 15, tipo="coccion", recurso="fogón", responsable="cocinero")
    core.produccion_real.obtener_plan(plan["id"]).configuracion_planificacion = {"hora_inicio": "08:00"}
    core.produccion_real._persistir()

    ocupacion = core.produccion_real.ocupacion_temporal_recursos(plan["id"])
    mesa = _buscar(ocupacion["recursos_fisicos"], "id_normalizado", "mesa_trabajo")
    fuego = _buscar(ocupacion["recursos_fisicos"], "id_normalizado", "fogones")

    assert len(ocupacion["bloques"]) == 3
    assert mesa["bloques_ocupacion"][0]["inicio_min"] == 8 * 60
    assert mesa["bloques_ocupacion"][0]["fin_min"] == 8 * 60 + 20
    assert len(fuego["bloques_ocupacion"]) == 2
    assert fuego["bloques_ocupacion"][0]["fin_min"] == fuego["bloques_ocupacion"][1]["inicio_min"]
    assert set(fuego["nombres_origen"]) == {"fuego", "fogón"}


def test_prioriza_planificacion_estimada_y_mantiene_integracion_con_inventario(tmp_path):
    _preparar_config(tmp_path, {"horno": 1, "mesa_trabajo": 2})
    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Planificado")
    tarea = core.produccion_real.anadir_tarea_manual(plan["id"], "Carrillera", prioridad=90)
    core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Preparar", 20, tipo="preparacion", recurso="mesa_trabajo", responsable="ayudante")
    core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Hornear", 60, tipo="produccion", recurso="horno", responsable="cocinero")
    plan_obj = core.produccion_real.obtener_plan(plan["id"])
    plan_obj.configuracion_planificacion = {"hora_inicio": "08:00", "jornada_horas": 7.5, "cocineros": 2}
    plan_obj.planificacion_inteligente = {
        "bloques": [
            {"clave": tarea["id"], "nombre": "Carrillera", "dia": 1, "inicio_min": 30, "fin_min": 50, "duracion_min": 20, "tipo_tiempo": "activo", "recurso": "mesa_trabajo", "datos": {"tarea_id": tarea["id"]}},
            {"clave": tarea["id"], "nombre": "Carrillera", "dia": 1, "inicio_min": 60, "fin_min": 120, "duracion_min": 60, "tipo_tiempo": "activo", "recurso": "horno", "datos": {"tarea_id": tarea["id"]}},
        ]
    }
    core.produccion_real._persistir()

    ocupacion = core.produccion_real.ocupacion_temporal_recursos(plan["id"])
    mesa = _buscar(ocupacion["recursos_fisicos"], "id_normalizado", "mesa_trabajo")
    horno = _buscar(ocupacion["recursos_fisicos"], "id_normalizado", "horno")

    assert mesa["capacidad"] == 2
    assert mesa["capacidad_confirmada"] is True
    assert mesa["bloques_ocupacion"][0]["inicio_min"] == 30
    assert mesa["bloques_ocupacion"][0]["origen_dato"] == "planificacion_estimada"
    assert horno["bloques_ocupacion"][0]["inicio_min"] == 60
    assert horno["bloques_ocupacion"][0]["responsable"] == "cocinero"
    assert ocupacion["resumen"]["bloques_planificados"] == 2


def test_prioriza_ejecucion_real_y_cronologia_coherente(tmp_path):
    _preparar_config(tmp_path, {"abatidor": 1})
    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Real")
    tarea = core.produccion_real.anadir_tarea_manual(plan["id"], "Salsa", prioridad=70)
    fase = core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Abatir", 25, tipo="abatido", recurso="abatidor", responsable="ayudante")
    plan_obj = core.produccion_real.obtener_plan(plan["id"])
    plan_obj.configuracion_planificacion = {"hora_inicio": "09:00"}
    tarea_obj = next(t for t in plan_obj.tareas if t.id == tarea["id"])
    fase_obj = next(f for f in tarea_obj.fases if f.id == fase["id"])
    fase_obj.hora_inicio_real = "2026-07-17T09:12:00"
    fase_obj.hora_fin_real = "2026-07-17T09:37:00"
    core.produccion_real._persistir()

    panel = core.produccion_real.panel_produccion(plan["id"])
    ocupacion = panel["ocupacion_temporal_recursos"]
    bloque = ocupacion["bloques"][0]

    assert panel["cronologia_operativa_prevista"]["tramos"][0]["inicio"]["tipo"] == "real"
    assert bloque["origen_dato"] == "ejecucion_real"
    assert bloque["inicio"]["texto"] == "Día 1 · 09:12"
    assert bloque["fin"]["texto"] == "Día 1 · 09:37"
    assert bloque["origen_referencia"] == "cronologia_operativa_prevista"


def test_caso_sin_recursos_no_falla(tmp_path):
    _preparar_config(tmp_path, {"horno": 1})
    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Vacío")

    ocupacion = core.produccion_real.ocupacion_temporal_recursos(plan["id"])

    assert ocupacion["bloques"] == []
    assert ocupacion["recursos_fisicos"] == []
    assert ocupacion["resumen"]["total_bloques"] == 0