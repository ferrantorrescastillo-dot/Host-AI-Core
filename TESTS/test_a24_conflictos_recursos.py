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


def _crear_plan(base: Path, nombre: str = "Conflictos"):
    core = HostAICore(base)
    plan = core.produccion_real.crear_plan_manual(nombre)
    return core, plan["id"]


def _tarea(core: HostAICore, plan_id: str, nombre: str, prioridad: int = 80) -> dict:
    return core.produccion_real.anadir_tarea_manual(plan_id, nombre, prioridad=prioridad)


def _set_planificacion(core: HostAICore, plan_id: str, bloques: list[dict], hora: str = "08:00") -> None:
    plan = core.produccion_real.obtener_plan(plan_id)
    plan.configuracion_planificacion = {"hora_inicio": hora, "cocineros": 2, "jornada_horas": 7.5}
    plan.planificacion_inteligente = {"bloques": bloques}
    core.produccion_real._persistir()


def _tipos(conflictos: dict) -> set[str]:
    return {c["tipo"] for c in conflictos.get("conflictos", [])}


def test_01_sin_conflictos(tmp_path):
    _preparar_config(tmp_path, {"horno": 1})
    core, plan_id = _crear_plan(tmp_path)
    t1 = _tarea(core, plan_id, "A")
    core.produccion_real.anadir_fase_manual(plan_id, t1["id"], "Hornear", 30, recurso="horno", responsable="cocinero")
    _set_planificacion(core, plan_id, [{"clave": t1["id"], "nombre": "A", "dia": 1, "inicio_min": 0, "fin_min": 30, "duracion_min": 30, "tipo_tiempo": "activo", "recurso": "horno"}])

    conflictos = core.produccion_real.conflictos_recursos(plan_id)
    assert conflictos["resumen"]["total"] == 0


def test_02_doble_asignacion_recurso(tmp_path):
    _preparar_config(tmp_path, {"horno": 2})
    core, plan_id = _crear_plan(tmp_path)
    a = _tarea(core, plan_id, "A")
    b = _tarea(core, plan_id, "B")
    core.produccion_real.anadir_fase_manual(plan_id, a["id"], "A1", 30, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, b["id"], "B1", 30, recurso="horno", responsable="ayudante")
    _set_planificacion(core, plan_id, [
        {"clave": a["id"], "nombre": "A", "dia": 1, "inicio_min": 10, "fin_min": 40, "duracion_min": 30, "tipo_tiempo": "activo", "recurso": "horno"},
        {"clave": b["id"], "nombre": "B", "dia": 1, "inicio_min": 10, "fin_min": 40, "duracion_min": 30, "tipo_tiempo": "activo", "recurso": "horno"},
    ])

    conflictos = core.produccion_real.conflictos_recursos(plan_id)
    assert "doble_asignacion_recurso" in _tipos(conflictos)


def test_03_doble_asignacion_responsable(tmp_path):
    _preparar_config(tmp_path, {"horno": 2, "mesa_trabajo": 2})
    core, plan_id = _crear_plan(tmp_path)
    a = _tarea(core, plan_id, "A")
    b = _tarea(core, plan_id, "B")
    core.produccion_real.anadir_fase_manual(plan_id, a["id"], "A1", 25, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, b["id"], "B1", 25, recurso="mesa_trabajo", responsable="cocinero")
    _set_planificacion(core, plan_id, [
        {"clave": a["id"], "nombre": "A", "dia": 1, "inicio_min": 0, "fin_min": 25, "duracion_min": 25, "tipo_tiempo": "activo", "recurso": "horno"},
        {"clave": b["id"], "nombre": "B", "dia": 1, "inicio_min": 5, "fin_min": 30, "duracion_min": 25, "tipo_tiempo": "activo", "recurso": "mesa_trabajo"},
    ])

    conflictos = core.produccion_real.conflictos_recursos(plan_id)
    assert "doble_asignacion_responsable" in _tipos(conflictos)


def test_04_capacidad_superada(tmp_path):
    _preparar_config(tmp_path, {"horno": 1})
    core, plan_id = _crear_plan(tmp_path)
    a = _tarea(core, plan_id, "A")
    b = _tarea(core, plan_id, "B")
    core.produccion_real.anadir_fase_manual(plan_id, a["id"], "A1", 40, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, b["id"], "B1", 40, recurso="horno", responsable="ayudante")
    _set_planificacion(core, plan_id, [
        {"clave": a["id"], "nombre": "A", "dia": 1, "inicio_min": 0, "fin_min": 40, "duracion_min": 40, "tipo_tiempo": "activo", "recurso": "horno"},
        {"clave": b["id"], "nombre": "B", "dia": 1, "inicio_min": 0, "fin_min": 40, "duracion_min": 40, "tipo_tiempo": "activo", "recurso": "horno"},
    ])

    conflictos = core.produccion_real.conflictos_recursos(plan_id)
    tipos = _tipos(conflictos)
    assert "capacidad_superada" in tipos
    assert any(c["severidad"] in {"alta", "crítica"} for c in conflictos["conflictos"] if c["tipo"] == "capacidad_superada")


def test_05_recurso_desconocido_y_sin_inventario(tmp_path):
    _preparar_config(tmp_path, {"horno": 1})
    core, plan_id = _crear_plan(tmp_path)
    t = _tarea(core, plan_id, "A")
    core.produccion_real.anadir_fase_manual(plan_id, t["id"], "A1", 20, recurso="recurso_raro", responsable="cocinero")
    _set_planificacion(core, plan_id, [{"clave": t["id"], "nombre": "A", "dia": 1, "inicio_min": 0, "fin_min": 20, "duracion_min": 20, "tipo_tiempo": "activo", "recurso": "recurso_raro"}])

    conflictos = core.produccion_real.conflictos_recursos(plan_id)
    tipos = _tipos(conflictos)
    assert "recurso_sin_inventario" in tipos or "recurso_desconocido" in tipos


def test_06_intervalo_invalido_y_datos_incompletos(tmp_path):
    _preparar_config(tmp_path, {"horno": 1})
    core, plan_id = _crear_plan(tmp_path)
    plan = core.produccion_real.obtener_plan(plan_id)
    ocupacion = core.produccion_real.ocupacion_temporal_recursos(plan_id)
    ocupacion.setdefault("datos_incompletos", []).extend([
        {"tipo": "ocupacion_intervalo_invalido", "recurso": "horno", "tarea": "A"},
        {"tipo": "ocupacion_incompleta", "recurso": "horno", "tarea": "A"},
    ])

    conflictos = core.inventario_recursos_produccion.construir_conflictos_plan(plan, ocupacion=ocupacion)
    tipos = _tipos(conflictos)
    assert "intervalo_invalido" in tipos
    assert "datos_incompletos" in tipos


def test_07_multiples_conflictos_prioridades_y_severidad(tmp_path):
    _preparar_config(tmp_path, {"horno": 1, "mesa_trabajo": 1})
    core, plan_id = _crear_plan(tmp_path)
    a = _tarea(core, plan_id, "A")
    b = _tarea(core, plan_id, "B")
    c = _tarea(core, plan_id, "C")
    core.produccion_real.anadir_fase_manual(plan_id, a["id"], "A1", 30, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, b["id"], "B1", 30, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, c["id"], "C1", 30, recurso="mesa_trabajo", responsable="cocinero")
    _set_planificacion(core, plan_id, [
        {"clave": a["id"], "nombre": "A", "dia": 1, "inicio_min": 0, "fin_min": 30, "duracion_min": 30, "tipo_tiempo": "activo", "recurso": "horno"},
        {"clave": b["id"], "nombre": "B", "dia": 1, "inicio_min": 0, "fin_min": 30, "duracion_min": 30, "tipo_tiempo": "activo", "recurso": "horno"},
        {"clave": c["id"], "nombre": "C", "dia": 1, "inicio_min": 0, "fin_min": 30, "duracion_min": 30, "tipo_tiempo": "activo", "recurso": "mesa_trabajo"},
    ])

    conflictos = core.produccion_real.conflictos_recursos(plan_id)
    assert conflictos["resumen"]["total"] >= 3
    severidades = {c["severidad"] for c in conflictos["conflictos"]}
    assert severidades & {"alta", "crítica"}


def test_08_integracion_con_simultaneidad_y_backend(tmp_path):
    _preparar_config(tmp_path, {"horno": 1, "mesa_trabajo": 1})
    core, plan_id = _crear_plan(tmp_path)
    a = _tarea(core, plan_id, "A")
    b = _tarea(core, plan_id, "B")
    core.produccion_real.anadir_fase_manual(plan_id, a["id"], "A1", 20, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, b["id"], "B1", 20, recurso="horno", responsable="ayudante")
    _set_planificacion(core, plan_id, [
        {"clave": a["id"], "nombre": "A", "dia": 1, "inicio_min": 10, "fin_min": 30, "duracion_min": 20, "tipo_tiempo": "activo", "recurso": "horno"},
        {"clave": b["id"], "nombre": "B", "dia": 1, "inicio_min": 10, "fin_min": 30, "duracion_min": 20, "tipo_tiempo": "activo", "recurso": "horno"},
    ])

    sim = core.produccion_real.simultaneidad_recursos(plan_id)
    conflictos = core.produccion_real.conflictos_recursos(plan_id)
    panel = core.produccion_real.panel_produccion(plan_id)

    assert sim["resumen"]["total_tramos"] >= 1
    assert conflictos["resumen"]["total"] >= 1
    assert "conflictos_recursos" in panel


def test_09_ids_trazabilidad_origen_y_tareas(tmp_path):
    _preparar_config(tmp_path, {"horno": 1})
    core, plan_id = _crear_plan(tmp_path)
    a = _tarea(core, plan_id, "A")
    b = _tarea(core, plan_id, "B")
    core.produccion_real.anadir_fase_manual(plan_id, a["id"], "A1", 20, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, b["id"], "B1", 20, recurso="horno", responsable="ayudante")
    _set_planificacion(core, plan_id, [
        {"clave": a["id"], "nombre": "A", "dia": 1, "inicio_min": 0, "fin_min": 20, "duracion_min": 20, "tipo_tiempo": "activo", "recurso": "horno"},
        {"clave": b["id"], "nombre": "B", "dia": 1, "inicio_min": 0, "fin_min": 20, "duracion_min": 20, "tipo_tiempo": "activo", "recurso": "horno"},
    ])

    conflictos = core.produccion_real.conflictos_recursos(plan_id)
    c = conflictos["conflictos"][0]
    assert c["id"].startswith("CFX-")
    assert isinstance(c["tareas_afectadas"], list)
    assert c["origen"]
    assert c["origen_temporal"] in {"real", "estimada", "mixto", "indeterminada"}


def test_10_clasificacion_severidad_consistente(tmp_path):
    _preparar_config(tmp_path, {"horno": 1})
    core, plan_id = _crear_plan(tmp_path)
    a = _tarea(core, plan_id, "A")
    b = _tarea(core, plan_id, "B")
    d = _tarea(core, plan_id, "D")
    core.produccion_real.anadir_fase_manual(plan_id, a["id"], "A1", 20, recurso="horno", responsable="cocinero")
    core.produccion_real.anadir_fase_manual(plan_id, b["id"], "B1", 20, recurso="horno", responsable="ayudante")
    core.produccion_real.anadir_fase_manual(plan_id, d["id"], "D1", 20, recurso="horno", responsable="jefe_cocina")
    _set_planificacion(core, plan_id, [
        {"clave": a["id"], "nombre": "A", "dia": 1, "inicio_min": 0, "fin_min": 20, "duracion_min": 20, "tipo_tiempo": "activo", "recurso": "horno"},
        {"clave": b["id"], "nombre": "B", "dia": 1, "inicio_min": 0, "fin_min": 20, "duracion_min": 20, "tipo_tiempo": "activo", "recurso": "horno"},
        {"clave": d["id"], "nombre": "D", "dia": 1, "inicio_min": 0, "fin_min": 20, "duracion_min": 20, "tipo_tiempo": "activo", "recurso": "horno"},
    ])

    conflictos = core.produccion_real.conflictos_recursos(plan_id)
    cap = [c for c in conflictos["conflictos"] if c["tipo"] == "capacidad_superada"]
    assert cap
    assert cap[0]["severidad"] == "crítica"
