from __future__ import annotations

from pathlib import Path

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI
from SERVICIOS.produccion_guiada_piloto_13 import ProduccionGuiadaPiloto13


def _crear_plan_cronologia(tmp_path: Path):
    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Plan cronologia", "2026-07-16", "Chef", estado="planificado")
    tarea = core.produccion_real.anadir_tarea_manual(plan["id"], "Demi-glace", prioridad=90)
    core.produccion_real.anadir_fase_manual(
        plan["id"],
        tarea["id"],
        "Preparar base",
        17,
        tipo="preparacion",
        recurso="mesa_trabajo",
        responsable="cocinero",
    )
    core.produccion_real.anadir_fase_manual(
        plan["id"],
        tarea["id"],
        "Reducir",
        28,
        tipo="coccion",
        recurso="fuego_2",
        responsable="cocinero",
    )
    core.produccion_real.planes[plan["id"]].configuracion_planificacion = {"hora_inicio": "09:00", "jornada_horas": 7.5, "cocineros": 2}
    core.produccion_real._persistir()
    return core, plan["id"], tarea["id"]


def test_cronologia_prevista_es_explicable_y_marca_estimacion(tmp_path: Path):
    core, plan_id, _ = _crear_plan_cronologia(tmp_path)
    panel = core.produccion_real.panel_produccion(plan_id)
    cronologia = panel["cronologia_operativa_prevista"]

    assert cronologia["resumen"]["total_tramos"] == 2
    assert cronologia["base_horaria"]["texto"] == "09:00 (estimado)"

    primer_tramo = cronologia["tramos"][0]
    assert primer_tramo["tarea"] == "Demi-glace"
    assert primer_tramo["fase"] == "Preparar base"
    assert primer_tramo["recurso"] == "mesa_trabajo"
    assert "Empieza aquí" in primer_tramo["inicio_razon"]
    assert primer_tramo["inicio"]["tipo"] == "estimado"
    assert primer_tramo["inicio"]["texto"].endswith("(estimado)")
    assert primer_tramo["inicio"]["texto"] == "09:00 (estimado)"

    segundo_tramo = cronologia["tramos"][1]
    assert segundo_tramo["inicio"]["texto"] == "09:15 (estimado)"
    assert segundo_tramo["inicio"]["precision_min"] == 5


def test_cronologia_diferencia_datos_reales_y_estimados(tmp_path: Path):
    core, plan_id, tarea_id = _crear_plan_cronologia(tmp_path)
    plan = core.produccion_real.planes[plan_id]
    tarea = next(t for t in plan.tareas if t.id == tarea_id)
    tarea.fases[0].hora_inicio_real = "2026-07-16T09:12:00"
    tarea.fases[0].hora_fin_real = "2026-07-16T09:29:00"
    core.produccion_real._persistir()

    panel = core.produccion_real.panel_produccion(plan_id)
    tramo_real = panel["cronologia_operativa_prevista"]["tramos"][0]

    assert tramo_real["inicio"]["tipo"] == "real"
    assert tramo_real["inicio"]["texto"] == "09:12"
    assert "hora_inicio_real" in tramo_real["informacion_real"]
    assert "hora_inicio_estimada" not in tramo_real["informacion_estimada"]


def test_cronologia_alerta_si_falta_duracion_sin_inventar(tmp_path: Path):
    core, plan_id, tarea_id = _crear_plan_cronologia(tmp_path)
    plan = core.produccion_real.planes[plan_id]
    tarea = next(t for t in plan.tareas if t.id == tarea_id)
    tarea.fases[0].duracion_min = 0
    tarea.fases[0].duracion_activa_min = 0
    tarea.fases[0].duracion_pasiva_min = 0
    core.produccion_real._persistir()

    panel = ProduccionGuiadaPiloto13(core).construir_panel(plan_id)
    tramos = panel["cronologia_tramos"]
    alertas = panel["cronologia_alertas"]

    assert tramos[0]["sin_datos_duracion"] is True
    assert tramos[0]["fin"]["tipo"] == "indeterminado"
    assert any("sin duración suficiente" in a for a in alertas)


def test_cronologia_toma_hora_base_desde_planificar_produccion_evento(tmp_path: Path):
    core = HostAICore(tmp_path)
    core.orquestador.resolver(SolicitudHostAI("registrar_escandallo", {
        "receta_id": "REC-CRONO",
        "nombre": "Receta Cronología",
        "raciones_base": 10,
        "lineas": [
            {
                "nombre": "Tomate",
                "cantidad": 2,
                "unidad": "kg",
                "articulo_id": "ART-CRONO",
                "coste_unitario": 0,
            }
        ],
    }))

    evento = core.orquestador.resolver(SolicitudHostAI("crear_evento", {
        "nombre": "Evento Cronología",
        "fecha": "2026-07-20",
        "pax": 40,
        "tipo": "catering",
    }))
    evento_id = evento.datos["evento"]["id"]

    servicio = core.orquestador.resolver(SolicitudHostAI("agregar_servicio_evento", {
        "evento_id": evento_id,
        "nombre": "Comida",
        "tipo": "comida",
        "hora_inicio": "13:00",
        "duracion_min": 120,
    }))
    servicio_id = servicio.datos["evento"]["servicios"][0]["id"]

    core.orquestador.resolver(SolicitudHostAI("agregar_pase_evento", {
        "evento_id": evento_id,
        "servicio_id": servicio_id,
        "nombre": "Principal",
        "hora_inicio": "13:30",
        "duracion_min": 35,
        "recetas": ["REC-CRONO"],
    }))

    plan = core.orquestador.resolver(SolicitudHostAI("planificar_produccion_real_evento", {
        "evento_id": evento_id,
        "hora_inicio": "09:00",
        "equipo_cocina": 2,
    }))
    assert plan.ok is True

    panel = core.produccion_real.panel_produccion(plan.datos["id"])
    cronologia = panel["cronologia_operativa_prevista"]

    assert cronologia["base_horaria"]["texto"] == "09:00 (estimado)"
    assert cronologia["base_horaria"]["tipo"] == "estimada_desde_plan"
