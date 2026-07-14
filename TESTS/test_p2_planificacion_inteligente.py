from pathlib import Path
from CORE.host_ai_core import HostAICore

def test_p2_planificacion(tmp_path):
    core=HostAICore(tmp_path)
    plan=core.produccion_real.crear_plan_manual("Producción prueba","2026-07-15","Ferran","")
    t1=core.produccion_real.anadir_tarea_manual(plan["id"],"Carrillera",90)
    core.produccion_real.anadir_fase_manual(plan["id"],t1["id"],"Preparar",60,"activo","mesa_trabajo","cocinero")
    core.produccion_real.anadir_fase_manual(plan["id"],t1["id"],"Cocción lenta",180,"pasivo","horno","cocinero")
    t2=core.produccion_real.anadir_tarea_manual(plan["id"],"Salsa",70)
    core.produccion_real.anadir_fase_manual(plan["id"],t2["id"],"Reducir",45,"activo","fuego","cocinero",t1["id"])
    r=core.produccion_real.planificar_inteligente(plan["id"],7.5,2,"08:00")
    assert r["planificacion"]["total_elaboraciones"]==2
    assert r["planificacion"]["minutos_activos"]==105
    assert r["planificacion"]["minutos_pasivos"]==180
    assert r["asignacion"]["total_asignaciones"]==2
    core2=HostAICore(tmp_path)
    rec=core2.produccion_real.obtener_plan(plan["id"])
    assert rec.estado=="planificado"
    assert rec.planificacion_inteligente["total_elaboraciones"]==2
