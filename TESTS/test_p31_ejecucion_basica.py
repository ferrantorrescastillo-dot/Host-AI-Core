from pathlib import Path
import time

from CORE.host_ai_core import HostAICore


def test_p31_ejecucion_basica_persistente(tmp_path: Path):
    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Producción prueba", "2026-07-12", "Ferran")
    tarea = core.produccion_real.anadir_tarea_manual(plan["id"], "Cortar verduras", 80)

    iniciado = core.produccion_real.iniciar_tarea(plan["id"], tarea["id"])
    assert iniciado["estado_ejecucion"] == "en_curso"
    assert iniciado["iniciado_en"]

    time.sleep(1.05)
    pausado = core.produccion_real.pausar_tarea(plan["id"], tarea["id"])
    assert pausado["estado_ejecucion"] == "pausada"
    assert pausado["tiempo_real_segundos"] >= 1

    core2 = HostAICore(tmp_path)
    reanudado = core2.produccion_real.reanudar_tarea(plan["id"], tarea["id"])
    assert reanudado["estado_ejecucion"] == "en_curso"
    assert reanudado["segundos_acumulados"] >= 1

    finalizado = core2.produccion_real.finalizar_tarea(plan["id"], tarea["id"])
    assert finalizado["estado_ejecucion"] == "finalizada"
    assert finalizado["finalizado_en"]

    resumen = core2.produccion_real.resumen_ejecucion(plan["id"])
    assert resumen["porcentaje_completado"] == 100.0
    assert resumen["estado_plan"] == "finalizado"

    core3 = HostAICore(tmp_path)
    recuperada = core3.produccion_real.estado_tarea(plan["id"], tarea["id"])
    assert recuperada["estado_ejecucion"] == "finalizada"
    assert recuperada["tiempo_real_segundos"] >= 1
