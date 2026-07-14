from CORE.host_ai_core import HostAICore


def test_p42_detecta_aplica_y_deshace_conflictos_recursos(tmp_path):
    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Recursos", "2026-07-21", "Ferran", "")
    t1 = core.produccion_real.anadir_tarea_manual(plan["id"], "Carrillera", 90)
    core.produccion_real.anadir_fase_manual(plan["id"], t1["id"], "Hornear carrillera", 120, "activo", "horno", "cocinero")
    t2 = core.produccion_real.anadir_tarea_manual(plan["id"], "Verduras", 80)
    core.produccion_real.anadir_fase_manual(plan["id"], t2["id"], "Hornear verduras", 60, "activo", "horno", "cocinero")

    p = core.produccion_real.obtener_plan(plan["id"])
    p.configuracion_planificacion = {"jornada_horas": 7.5, "cocineros": 2, "hora_inicio": "08:00"}
    p.planificacion_inteligente = {
        "version": "test",
        "bloques": [
            {"clave": t1["id"], "nombre": "Carrillera", "dia": 1, "inicio_min": 0, "fin_min": 120, "duracion_min": 120, "tipo_tiempo": "activo", "recurso": "horno", "datos": {"prioridad_num": 90}},
            {"clave": t2["id"], "nombre": "Verduras", "dia": 1, "inicio_min": 30, "fin_min": 90, "duracion_min": 60, "tipo_tiempo": "activo", "recurso": "horno", "datos": {"prioridad_num": 80}},
        ],
    }
    core.produccion_real._persistir()

    propuesta = core.produccion_real.proponer_optimizacion_recursos(plan["id"], {"horno": 1})
    assert len(propuesta["conflictos_originales"]) >= 1
    assert propuesta["conflictos_optimizados"] == []
    assert propuesta["movimientos"]

    aplicada = core.produccion_real.aplicar_optimizacion_recursos(plan["id"])
    assert aplicada["estado"] == "aplicada"
    rec = HostAICore(tmp_path).produccion_real.obtener_plan(plan["id"])
    assert rec.historial_optimizacion_recursos
    bloques = [b for b in rec.planificacion_inteligente["bloques"] if b.get("recurso") == "horno"]
    bloques = sorted(bloques, key=lambda b: b["inicio_min"])
    assert bloques[0]["fin_min"] <= bloques[1]["inicio_min"]

    core2 = HostAICore(tmp_path)
    deshecha = core2.produccion_real.deshacer_ultima_optimizacion_recursos(plan["id"])
    assert deshecha["estado"] == "deshecha"
    rec2 = HostAICore(tmp_path).produccion_real.obtener_plan(plan["id"])
    assert rec2.planificacion_inteligente["bloques"][1]["inicio_min"] == 30
