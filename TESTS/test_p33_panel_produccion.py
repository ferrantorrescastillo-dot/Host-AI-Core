from pathlib import Path
from CORE.host_ai_core import HostAICore


def test_p33_panel_produccion(tmp_path: Path):
    core=HostAICore(tmp_path)
    plan=core.produccion_real.crear_plan_manual("Turno prueba","2026-07-16","Ferran","")
    t1=core.produccion_real.anadir_tarea_manual(plan["id"],"Carrillera",90)
    core.produccion_real.anadir_fase_manual(plan["id"],t1["id"],"Preparar",60,"activo","mesa","cocinero")
    t2=core.produccion_real.anadir_tarea_manual(plan["id"],"Salsa",70)
    core.produccion_real.anadir_fase_manual(plan["id"],t2["id"],"Reducir",45,"activo","fuego","cocinero")
    core.produccion_real.planificar_inteligente(plan["id"],7.5,2,"08:00")
    core.produccion_real.iniciar_tarea(plan["id"],t1["id"])
    core.produccion_real.actualizar_progreso_tarea(plan["id"],t1["id"],50)
    core.produccion_real.registrar_incidencia_tarea(plan["id"],t2["id"],"bloqueo","Falta fuego",10)
    core.produccion_real.anadir_item_checklist(plan["id"],t1["id"],"Envasar")

    panel=core.produccion_real.panel_produccion(plan["id"])
    assert panel["total_tareas"]==2
    assert panel["estados"]["en_curso"]==1
    assert panel["metricas_turno"]["incidencias"]==1
    assert panel["metricas_turno"]["bloqueos_activos"]==1
    assert panel["metricas_turno"]["checklist_total"]==1
    assert any(c["tareas"] for c in panel["cocineros"])

    stats=core.produccion_real.estadisticas_turno(plan["id"])
    assert stats["total_tareas"]==2
    assert stats["estado"]=="en_curso"

    core2=HostAICore(tmp_path)
    panel2=core2.produccion_real.panel_produccion(plan["id"])
    assert panel2["metricas_turno"]["incidencias"]==1
    assert panel2["metricas_turno"]["bloqueos_activos"]==1
