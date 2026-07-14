from pathlib import Path
from datetime import datetime, timedelta

from CORE.host_ai_core import HostAICore


def test_p32_seguimiento_servicio_persistente(tmp_path: Path):
    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Servicio P3.2", "2026-07-13", "Ferran")
    tarea = core.produccion_real.anadir_tarea_manual(plan["id"], "Preparar ensaladilla", 90)
    core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Cocer patata", 20, "activo", "fuego", "Cocinero 1")
    core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Enfriar", 10, "pasivo", "abatidor", "Cocinero 1")

    item1 = core.produccion_real.anadir_item_checklist(plan["id"], tarea["id"], "Patata cocida")
    item2 = core.produccion_real.anadir_item_checklist(plan["id"], tarea["id"], "Mayonesa incorporada")
    core.produccion_real.marcar_item_checklist(plan["id"], tarea["id"], item1["id"], True)

    core.produccion_real.iniciar_tarea(plan["id"], tarea["id"])
    obj = core.produccion_real.obtener_plan(plan["id"]).tareas[0]
    obj.cronometro_iniciado_en = (datetime.now() - timedelta(minutes=8)).isoformat(timespec="seconds")
    core.produccion_real._persistir()

    progreso = core.produccion_real.actualizar_progreso_tarea(plan["id"], tarea["id"], 45)
    assert progreso["porcentaje_avance"] >= 45
    assert progreso["tiempo_previsto_min"] == 30
    assert progreso["tiempo_restante_estimado_min"] <= 22.1
    assert progreso["checklist_completado"] == 1
    assert progreso["checklist_pendiente"] == 1

    incidencia = core.produccion_real.registrar_incidencia_tarea(
        plan["id"], tarea["id"], "bloqueo", "Falta mayonesa", 12
    )
    assert incidencia["tipo"] == "bloqueo"
    estado = core.produccion_real.estado_tarea(plan["id"], tarea["id"])
    assert estado["bloqueo"] == "Falta mayonesa"
    assert estado["retraso_min"] == 12
    assert len(estado["incidencias"]) == 1

    alertas = core.produccion_real.alertas_ejecucion(plan["id"])
    tipos = {a["tipo"] for a in alertas}
    assert "bloqueo" in tipos
    assert "retraso" in tipos

    core.produccion_real.replanificar_tarea_manual(
        plan["id"], tarea["id"], prioridad=100, responsable="Ferran", notas="Prioridad absoluta"
    )
    core.produccion_real.resolver_bloqueo_tarea(plan["id"], tarea["id"], "Mayonesa localizada")

    core2 = HostAICore(tmp_path)
    recuperada = core2.produccion_real.estado_tarea(plan["id"], tarea["id"])
    assert recuperada["prioridad"] == 100
    assert recuperada["bloqueo"] == ""
    assert recuperada["observaciones_ejecucion"] == "Mayonesa localizada"
    assert recuperada["checklist_total"] == 2
    assert recuperada["checklist_completado"] == 1
    assert recuperada["retraso_min"] == 12

    core2.produccion_real.marcar_item_checklist(plan["id"], tarea["id"], item2["id"], True)
    final = core2.produccion_real.finalizar_tarea(plan["id"], tarea["id"])
    assert final["estado_ejecucion"] == "finalizada"
    assert final["porcentaje_avance"] == 100.0
    assert final["checklist_pendiente"] == 0

    resumen = core2.produccion_real.resumen_ejecucion(plan["id"])
    assert resumen["porcentaje_completado"] == 100.0
    assert resumen["tareas_pendientes"] == []
