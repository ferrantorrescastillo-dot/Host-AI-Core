from CORE.host_ai_core import HostAICore


def test_p43_genera_aplica_persiste_y_deshace_recomendaciones(tmp_path):
    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Turno prueba", "2026-07-22", "Ferran", "")
    tarea = core.produccion_real.anadir_tarea_manual(plan["id"], "Carrillera", 50)
    core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Preparar", 30, "activo", "mesa_trabajo", "Cocinero 1")
    core.produccion_real.anadir_fase_manual(plan["id"], tarea["id"], "Reposar", 60, "pasivo", "mesa_trabajo", "Cocinero 1")
    core.produccion_real.anadir_item_checklist(plan["id"], tarea["id"], "Etiquetar")
    core.produccion_real.actualizar_progreso_tarea(plan["id"], tarea["id"], 80)
    core.produccion_real.registrar_incidencia_tarea(plan["id"], tarea["id"], "bloqueo", "Falta abatidor", 20)

    propuesta = core.produccion_real.generar_recomendaciones_inteligentes(plan["id"])
    assert propuesta["version"] == "6.0.4-P4.3"
    assert propuesta["total"] >= 3
    assert any(r["tipo"] == "cuello_botella" for r in propuesta["recomendaciones"])
    assert any(r["tipo"] == "retraso" for r in propuesta["recomendaciones"])
    assert any(r["tipo"] == "checklist" for r in propuesta["recomendaciones"])
    assert propuesta["aplicables"] >= 1

    aplicada = core.produccion_real.aplicar_recomendaciones(plan["id"])
    assert aplicada["total_aplicadas"] >= 1
    actualizado = core.produccion_real.obtener_plan(plan["id"])
    assert actualizado.tareas[0].prioridad > 50
    assert actualizado.historial_recomendaciones

    recargado = HostAICore(tmp_path).produccion_real.obtener_plan(plan["id"])
    assert recargado.historial_recomendaciones
    assert recargado.tareas[0].prioridad > 50

    core2 = HostAICore(tmp_path)
    deshecha = core2.produccion_real.deshacer_ultimas_recomendaciones(plan["id"])
    assert deshecha["estado"] == "deshecha"
    final = HostAICore(tmp_path).produccion_real.obtener_plan(plan["id"])
    assert final.tareas[0].prioridad == 50
