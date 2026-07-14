from CORE.host_ai_core import HostAICore


def test_p41_propuesta_aplicar_y_deshacer(tmp_path):
    core=HostAICore(tmp_path)
    plan=core.produccion_real.crear_plan_manual("Optimización básica","2026-07-20","Ferran","")
    corta=core.produccion_real.anadir_tarea_manual(plan["id"],"Guarnición",70)
    core.produccion_real.anadir_fase_manual(plan["id"],corta["id"],"Preparar",30,"activo","mesa","cocinero")
    larga=core.produccion_real.anadir_tarea_manual(plan["id"],"Carrillera",70)
    core.produccion_real.anadir_fase_manual(plan["id"],larga["id"],"Preparar",30,"activo","mesa","cocinero")
    core.produccion_real.anadir_fase_manual(plan["id"],larga["id"],"Cocción",180,"pasivo","horno","cocinero")
    core.produccion_real.planificar_inteligente(plan["id"],7.5,1,"08:00")
    propuesta=core.produccion_real.proponer_optimizacion_basica(plan["id"])
    assert propuesta["duracion_optimizada_min"] <= propuesta["duracion_original_min"]
    assert propuesta["ahorro_min"] >= 0
    original=propuesta["planificacion_original"]
    aplicada=core.produccion_real.aplicar_optimizacion_basica(plan["id"])
    assert aplicada["estado"]=="aplicada"
    rec=HostAICore(tmp_path).produccion_real.obtener_plan(plan["id"])
    assert rec.historial_optimizacion
    core2=HostAICore(tmp_path)
    deshecha=core2.produccion_real.deshacer_ultima_optimizacion(plan["id"])
    assert deshecha["estado"]=="deshecha"
    rec2=HostAICore(tmp_path).produccion_real.obtener_plan(plan["id"])
    assert rec2.planificacion_inteligente["bloques"]==original["bloques"]
