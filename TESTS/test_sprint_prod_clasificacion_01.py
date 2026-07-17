from __future__ import annotations

from CORE.host_ai_core import HostAICore


def test_clasificacion_no_exclusiva_en_panel_produccion(tmp_path):
    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Plan clasificación")
    plan_id = plan["id"]

    carrillera = core.produccion_real.anadir_tarea_manual(plan_id, "Carrillera", prioridad=90, origen="escandallo_evento")
    demi = core.produccion_real.anadir_tarea_manual(plan_id, "Demi-glace", prioridad=90, origen="escandallo_evento")
    pure = core.produccion_real.anadir_tarea_manual(plan_id, "Puré", prioridad=60, origen="escandallo_evento")
    vinagreta = core.produccion_real.anadir_tarea_manual(plan_id, "Vinagreta", prioridad=40, origen="escandallo_evento")
    core.produccion_real.anadir_tarea_manual(plan_id, "Carga, transporte y montaje", prioridad=70, origen="logistica")

    core.produccion_real.anadir_fase_manual(plan_id, carrillera["id"], "Preparar", 45, tipo="preparacion")
    core.produccion_real.anadir_fase_manual(plan_id, carrillera["id"], "Cocción lenta", 180, tipo="coccion")
    core.produccion_real.anadir_fase_manual(plan_id, demi["id"], "Preparar base", 30, tipo="preparacion")
    core.produccion_real.anadir_fase_manual(plan_id, demi["id"], "Reducir", 170, tipo="coccion")
    core.produccion_real.anadir_fase_manual(plan_id, pure["id"], "Cocer", 45, tipo="coccion")
    core.produccion_real.anadir_fase_manual(plan_id, pure["id"], "Triturar", 30, tipo="produccion")
    core.produccion_real.anadir_fase_manual(plan_id, vinagreta["id"], "Mezclar", 15, tipo="preparacion")

    core.produccion_real.registrar_incidencia_tarea(plan_id, carrillera["id"], "bloqueo", "Stock insuficiente", 0, "media", "pausa", "", "")

    panel = core.produccion_real.panel_produccion(plan_id)
    clasificacion = panel["clasificacion_jornada"]
    resumen = clasificacion["resumen"]
    detalle = {item["titulo"]: item for item in clasificacion["detalle"]}

    assert resumen == {"criticas": 2, "largas": 2, "medias": 1, "rapidas": 1}
    assert detalle["Carrillera"]["grupos"] == ["critica", "larga"]
    assert "Stock insuficiente" in detalle["Carrillera"]["razones"]
    assert detalle["Demi-glace"]["grupos"] == ["critica", "larga"]
    assert "prioridad operativa muy urgente" in detalle["Demi-glace"]["razones"]
    assert detalle["Puré"]["grupos"] == ["media"]
    assert detalle["Vinagreta"]["grupos"] == ["rapida"]
    assert "Carga, transporte y montaje" not in detalle