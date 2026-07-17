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


def _crear_plan(base: Path, nombre: str = "Simultaneidad"):
    core = HostAICore(base)
    plan = core.produccion_real.crear_plan_manual(nombre)
    return core, plan["id"]


def _primera_tarea(core: HostAICore, plan_id: str, nombre: str = "T1", prioridad: int = 80) -> dict:
    return core.produccion_real.anadir_tarea_manual(plan_id, nombre, prioridad=prioridad)


def _set_hora_inicio(core: HostAICore, plan_id: str, hora: str) -> None:
    core.produccion_real.obtener_plan(plan_id).configuracion_planificacion = {"hora_inicio": hora}
    core.produccion_real._persistir()


def test_01_plan_sin_ocupaciones(tmp_path):
    _preparar_config(tmp_path)
    core, plan_id = _crear_plan(tmp_path, "Vacio")
    sim = core.produccion_real.simultaneidad_recursos(plan_id)
    assert sim["tramos"] == []
    assert sim["resumen"]["total_tramos"] == 0


def test_02_una_unica_ocupacion(tmp_path):
    _preparar_config(tmp_path, {"horno": 1})
    core, plan_id = _crear_plan(tmp_path)
    t = _primera_tarea(core, plan_id, "Carrillera")
    core.produccion_real.anadir_fase_manual(plan_id, t["id"], "Hornear", 60, recurso="horno", responsable="cocinero")
    _set_hora_inicio(core, plan_id, "09:00")
    sim = core.produccion_real.simultaneidad_recursos(plan_id)
    assert sim["resumen"]["total_tramos"] == 1
    assert sim["tramos"][0]["cantidad_total_ocupaciones"] == 1


def test_03_dos_ocupaciones_consecutivas_sin_solape_y_frontera_exacta(tmp_path):
    _preparar_config(tmp_path, {"horno": 1})
    core, plan_id = _crear_plan(tmp_path)
    t = _primera_tarea(core, plan_id, "Bases")
    core.produccion_real.anadir_fase_manual(plan_id, t["id"], "Hornear 1", 30, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, t["id"], "Hornear 2", 30, recurso="horno", responsable="cocinero")
    _set_hora_inicio(core, plan_id, "10:00")
    sim = core.produccion_real.simultaneidad_recursos(plan_id)
    assert [t["cantidad_total_ocupaciones"] for t in sim["tramos"]] == [1, 1]
    assert sim["tramos"][0]["fin_min"] == sim["tramos"][1]["inicio_min"]


def test_04_dos_ocupaciones_con_solape_parcial(tmp_path):
    _preparar_config(tmp_path, {"horno": 1, "mesa_trabajo": 1})
    core, plan_id = _crear_plan(tmp_path)
    a = _primera_tarea(core, plan_id, "A", 90)
    b = _primera_tarea(core, plan_id, "B", 80)
    core.produccion_real.anadir_fase_manual(plan_id, a["id"], "A1", 40, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, b["id"], "B1", 40, recurso="mesa_trabajo", responsable="ayudante")
    plan = core.produccion_real.obtener_plan(plan_id)
    plan.configuracion_planificacion = {"hora_inicio": "08:00"}
    plan.planificacion_inteligente = {
        "bloques": [
            {"clave": a["id"], "nombre": "A", "dia": 1, "inicio_min": 0, "fin_min": 40, "duracion_min": 40, "tipo_tiempo": "activo", "recurso": "horno"},
            {"clave": b["id"], "nombre": "B", "dia": 1, "inicio_min": 20, "fin_min": 60, "duracion_min": 40, "tipo_tiempo": "activo", "recurso": "mesa_trabajo"},
        ]
    }
    core.produccion_real._persistir()
    sim = core.produccion_real.simultaneidad_recursos(plan_id)
    assert any(t["cantidad_total_ocupaciones"] == 2 for t in sim["tramos"])


def test_05_dos_ocupaciones_mismo_inicio_fin(tmp_path):
    _preparar_config(tmp_path, {"horno": 1, "fogones": 1})
    core, plan_id = _crear_plan(tmp_path)
    a = _primera_tarea(core, plan_id, "A")
    b = _primera_tarea(core, plan_id, "B")
    core.produccion_real.anadir_fase_manual(plan_id, a["id"], "A1", 30, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, b["id"], "B1", 30, recurso="fuego", responsable="cocinero")
    plan = core.produccion_real.obtener_plan(plan_id)
    plan.configuracion_planificacion = {"hora_inicio": "08:00"}
    plan.planificacion_inteligente = {
        "bloques": [
            {"clave": a["id"], "nombre": "A", "dia": 1, "inicio_min": 10, "fin_min": 40, "duracion_min": 30, "tipo_tiempo": "activo", "recurso": "horno"},
            {"clave": b["id"], "nombre": "B", "dia": 1, "inicio_min": 10, "fin_min": 40, "duracion_min": 30, "tipo_tiempo": "activo", "recurso": "fuego"},
        ]
    }
    core.produccion_real._persistir()
    sim = core.produccion_real.simultaneidad_recursos(plan_id)
    assert sim["tramos"][0]["cantidad_total_ocupaciones"] == 2


def test_06_tres_ocupaciones_parcialmente_solapadas_y_maximo(tmp_path):
    _preparar_config(tmp_path, {"horno": 1, "mesa_trabajo": 1, "fogones": 1})
    core, plan_id = _crear_plan(tmp_path)
    a = _primera_tarea(core, plan_id, "A", 90)
    b = _primera_tarea(core, plan_id, "B", 80)
    c = _primera_tarea(core, plan_id, "C", 70)
    core.produccion_real.anadir_fase_manual(plan_id, a["id"], "A1", 40, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, b["id"], "B1", 40, recurso="mesa_trabajo", responsable="ayudante")
    core.produccion_real.anadir_fase_manual(plan_id, c["id"], "C1", 40, recurso="fuego", responsable="jefe_cocina")
    plan = core.produccion_real.obtener_plan(plan_id)
    plan.configuracion_planificacion = {"hora_inicio": "08:00"}
    plan.planificacion_inteligente = {
        "bloques": [
            {"clave": a["id"], "nombre": "A", "dia": 1, "inicio_min": 0, "fin_min": 40, "duracion_min": 40, "tipo_tiempo": "activo", "recurso": "horno"},
            {"clave": b["id"], "nombre": "B", "dia": 1, "inicio_min": 10, "fin_min": 50, "duracion_min": 40, "tipo_tiempo": "activo", "recurso": "mesa_trabajo"},
            {"clave": c["id"], "nombre": "C", "dia": 1, "inicio_min": 20, "fin_min": 60, "duracion_min": 40, "tipo_tiempo": "activo", "recurso": "fuego"},
        ]
    }
    core.produccion_real._persistir()
    sim = core.produccion_real.simultaneidad_recursos(plan_id)
    assert core.produccion_real.maximo_nivel_simultaneidad(plan_id) == 3
    assert any(t["cantidad_total_ocupaciones"] == 3 for t in sim["tramos"])


def test_07_varios_recursos_fisicos_y_responsables(tmp_path):
    _preparar_config(tmp_path, {"horno": 1, "mesa_trabajo": 1})
    core, plan_id = _crear_plan(tmp_path)
    a = _primera_tarea(core, plan_id, "A")
    b = _primera_tarea(core, plan_id, "B")
    core.produccion_real.anadir_fase_manual(plan_id, a["id"], "A1", 20, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, b["id"], "B1", 20, recurso="mesa_trabajo", responsable="ayudante")
    plan = core.produccion_real.obtener_plan(plan_id)
    plan.configuracion_planificacion = {"hora_inicio": "09:00"}
    plan.planificacion_inteligente = {
        "bloques": [
            {"clave": a["id"], "nombre": "A", "dia": 1, "inicio_min": 10, "fin_min": 30, "duracion_min": 20, "tipo_tiempo": "activo", "recurso": "horno"},
            {"clave": b["id"], "nombre": "B", "dia": 1, "inicio_min": 10, "fin_min": 30, "duracion_min": 20, "tipo_tiempo": "activo", "recurso": "mesa_trabajo"},
        ]
    }
    core.produccion_real._persistir()
    sim = core.produccion_real.simultaneidad_recursos(plan_id)
    tramo = sim["tramos"][0]
    assert set(tramo["recursos_fisicos_activos"]) == {"horno", "mesa_trabajo"}
    assert set(tramo["responsables_activos"]) == {"cocinero", "ayudante"}


def test_08_alias_recurso_sin_duplicacion(tmp_path):
    _preparar_config(tmp_path, {"fogones": 2})
    core, plan_id = _crear_plan(tmp_path)
    a = _primera_tarea(core, plan_id, "A")
    b = _primera_tarea(core, plan_id, "B")
    core.produccion_real.anadir_fase_manual(plan_id, a["id"], "A1", 20, recurso="fuego", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, b["id"], "B1", 20, recurso="fogón", responsable="cocinero")
    _set_hora_inicio(core, plan_id, "09:00")
    sim = core.produccion_real.simultaneidad_recursos(plan_id)
    assert sim["tramos"][0]["recursos_fisicos_activos"] == ["fogones"]


def test_09_ocupaciones_estimadas_reales_y_mixtas(tmp_path):
    _preparar_config(tmp_path, {"horno": 1, "mesa_trabajo": 1})
    core, plan_id = _crear_plan(tmp_path)
    a = _primera_tarea(core, plan_id, "A")
    b = _primera_tarea(core, plan_id, "B")
    fa = core.produccion_real.anadir_fase_manual(plan_id, a["id"], "A1", 40, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, b["id"], "B1", 40, recurso="mesa_trabajo", responsable="ayudante")
    plan = core.produccion_real.obtener_plan(plan_id)
    plan.configuracion_planificacion = {"hora_inicio": "08:00"}
    plan.planificacion_inteligente = {
        "bloques": [
            {"clave": a["id"], "nombre": "A", "dia": 1, "inicio_min": 10, "fin_min": 50, "duracion_min": 40, "tipo_tiempo": "activo", "recurso": "horno"},
            {"clave": b["id"], "nombre": "B", "dia": 1, "inicio_min": 35, "fin_min": 60, "duracion_min": 25, "tipo_tiempo": "activo", "recurso": "mesa_trabajo"},
        ]
    }
    tarea_a = next(t for t in plan.tareas if t.id == a["id"])
    fase_a = next(f for f in tarea_a.fases if f.id == fa["id"])
    fase_a.hora_inicio_real = "2026-07-17T00:25:00"
    fase_a.hora_fin_real = "2026-07-17T00:55:00"
    core.produccion_real._persistir()
    sim = core.produccion_real.simultaneidad_recursos(plan_id)
    assert any(t["origen_temporal"] == "real" for t in sim["tramos"])
    assert any(t["origen_temporal"] == "estimada" for t in sim["tramos"])
    assert any(t["origen_temporal"] == "mixto" for t in sim["tramos"])


def test_10_intervalo_invalido_o_incompleto_no_rompe(tmp_path):
    _preparar_config(tmp_path, {"horno": 1})
    core, plan_id = _crear_plan(tmp_path)
    t = _primera_tarea(core, plan_id, "A")
    fase = core.produccion_real.anadir_fase_manual(plan_id, t["id"], "A1", 1, recurso="horno", responsable="cocinero")
    _set_hora_inicio(core, plan_id, "09:00")
    plan = core.produccion_real.obtener_plan(plan_id)
    tarea = next(x for x in plan.tareas if x.id == t["id"])
    fase_obj = next(x for x in tarea.fases if x.id == fase["id"])
    fase_obj.duracion_min = 0
    fase_obj.hora_inicio_real = "2026-07-17T09:00:00"
    fase_obj.hora_fin_real = "2026-07-17T09:00:00"
    core.produccion_real._persistir()
    sim = core.produccion_real.simultaneidad_recursos(plan_id)
    assert sim["tramos"] == []
    assert sim["datos_incompletos"]


def test_11_consulta_por_instante_intervalo_umbral_y_orden(tmp_path):
    _preparar_config(tmp_path, {"horno": 1, "mesa_trabajo": 1, "fogones": 1})
    core, plan_id = _crear_plan(tmp_path)
    a = _primera_tarea(core, plan_id, "A")
    b = _primera_tarea(core, plan_id, "B")
    c = _primera_tarea(core, plan_id, "C")
    core.produccion_real.anadir_fase_manual(plan_id, a["id"], "A1", 40, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, b["id"], "B1", 40, recurso="mesa_trabajo", responsable="ayudante")
    core.produccion_real.anadir_fase_manual(plan_id, c["id"], "C1", 20, recurso="fuego", responsable="jefe_cocina")
    plan = core.produccion_real.obtener_plan(plan_id)
    plan.configuracion_planificacion = {"hora_inicio": "08:00"}
    plan.planificacion_inteligente = {
        "bloques": [
            {"clave": a["id"], "nombre": "A", "dia": 1, "inicio_min": 0, "fin_min": 40, "duracion_min": 40, "tipo_tiempo": "activo", "recurso": "horno"},
            {"clave": b["id"], "nombre": "B", "dia": 1, "inicio_min": 20, "fin_min": 60, "duracion_min": 40, "tipo_tiempo": "activo", "recurso": "mesa_trabajo"},
            {"clave": c["id"], "nombre": "C", "dia": 1, "inicio_min": 30, "fin_min": 50, "duracion_min": 20, "tipo_tiempo": "activo", "recurso": "fuego"},
        ]
    }
    core.produccion_real._persistir()

    sim = core.produccion_real.simultaneidad_recursos(plan_id)
    instante = core.produccion_real.simultaneidad_recursos_en_instante(plan_id, 35)
    intervalo = core.produccion_real.simultaneidad_recursos_en_intervalo(plan_id, 25, 45)
    umbral = core.produccion_real.tramos_simultaneidad_por_umbral(plan_id, 2)

    assert instante["cantidad_tramos"] == 1
    assert set(core.produccion_real.recursos_activos_simultaneos(plan_id, instante_min=35)) == {"horno", "mesa_trabajo", "fogones"}
    assert set(core.produccion_real.tareas_activas_simultaneas(plan_id, instante_min=35)) == {"A", "B", "C"}
    assert set(core.produccion_real.responsables_activos_simultaneos(plan_id, instante_min=35)) == {"cocinero", "ayudante", "jefe_cocina"}
    assert intervalo["cantidad_tramos"] >= 1
    assert all(t["cantidad_total_ocupaciones"] >= 2 for t in umbral)
    assert sim["tramos"] == sorted(sim["tramos"], key=lambda t: (t["dia"], t["inicio_min"], t["fin_min"]))


def test_12_integracion_a22_y_panel_backend_sin_cambiar_recomendacion(tmp_path):
    _preparar_config(tmp_path, {"horno": 1, "mesa_trabajo": 1})
    core, plan_id = _crear_plan(tmp_path)
    a = _primera_tarea(core, plan_id, "Carrillera", 90)
    b = _primera_tarea(core, plan_id, "Costillar", 80)
    core.produccion_real.anadir_fase_manual(plan_id, a["id"], "Hornear", 60, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, b["id"], "Preparar", 60, recurso="mesa_trabajo", responsable="ayudante")
    _set_hora_inicio(core, plan_id, "09:00")

    panel = core.produccion_real.panel_produccion(plan_id)
    recomendacion = core.produccion_real.siguiente_tarea_recomendada(plan_id)

    assert "ocupacion_temporal_recursos" in panel
    assert "simultaneidad_recursos" in panel
    assert panel["simultaneidad_recursos"]["resumen"]["total_tramos"] >= 1
    assert recomendacion["codigo"] in {"SUGERIDA", "SIN_TAREAS", "SIN_PLANIFICACION"}
