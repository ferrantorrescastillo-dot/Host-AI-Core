from __future__ import annotations

from CORE.host_ai_core import HostAICore


def test_detecta_cuello_futuro_de_recurso_y_personal_con_datos_reales(tmp_path):
    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Plan cuellos")
    plan_id = plan["id"]

    carrillera = core.produccion_real.anadir_tarea_manual(plan_id, "Carrillera", prioridad=90, origen="escandallo_evento")
    costillar = core.produccion_real.anadir_tarea_manual(plan_id, "Costillar", prioridad=80, origen="escandallo_evento")
    salsa = core.produccion_real.anadir_tarea_manual(plan_id, "Salsa", prioridad=70, origen="escandallo_evento")

    core.produccion_real.anadir_fase_manual(plan_id, carrillera["id"], "Hornear", 120, tipo="produccion", recurso="horno")
    core.produccion_real.anadir_fase_manual(plan_id, costillar["id"], "Hornear", 60, tipo="produccion", recurso="horno")
    core.produccion_real.anadir_fase_manual(plan_id, salsa["id"], "Reducir", 45, tipo="produccion", recurso="fuego", dependencia=carrillera["id"])

    plan_obj = core.produccion_real.obtener_plan(plan_id)
    plan_obj.configuracion_planificacion = {"jornada_horas": 7.5, "cocineros": 1, "hora_inicio": "08:00"}
    plan_obj.planificacion_inteligente = {
        "bloques": [
            {"clave": carrillera["id"], "nombre": "Carrillera", "dia": 1, "inicio_min": 0, "fin_min": 120, "duracion_min": 120, "tipo_tiempo": "activo", "recurso": "horno", "dependencias": [], "datos": {"prioridad_num": 90}},
            {"clave": costillar["id"], "nombre": "Costillar", "dia": 1, "inicio_min": 45, "fin_min": 105, "duracion_min": 60, "tipo_tiempo": "activo", "recurso": "horno", "dependencias": [], "datos": {"prioridad_num": 80}},
            {"clave": salsa["id"], "nombre": "Salsa", "dia": 1, "inicio_min": 125, "fin_min": 170, "duracion_min": 45, "tipo_tiempo": "activo", "recurso": "fuego", "dependencias": [carrillera["id"]], "datos": {"prioridad_num": 70}},
            {"clave": "SALSA-ACABADO", "nombre": "Salsa acabado", "dia": 1, "inicio_min": 175, "fin_min": 205, "duracion_min": 30, "tipo_tiempo": "activo", "recurso": "mesa_trabajo", "dependencias": [carrillera["id"]], "datos": {"prioridad_num": 70}},
        ]
    }
    plan_obj.asignacion_recursos = {
        "carga_por_cocinero": {"Cocinero 1": 500},
        "resumen": {"capacidad_por_cocinero_min": 450},
        "asignaciones": [
            {"cocinero": "Cocinero 1", "dia": 1, "inicio_min": 0, "fin_min": 120, "elaboracion": "Carrillera"},
            {"cocinero": "Cocinero 1", "dia": 1, "inicio_min": 45, "fin_min": 105, "elaboracion": "Costillar"},
            {"cocinero": "Cocinero 1", "dia": 1, "inicio_min": 125, "fin_min": 170, "elaboracion": "Salsa"},
        ],
    }

    panel = core.produccion_real.panel_produccion(plan_id)
    cuellos = panel["cuellos_botella_previstos"]
    resumen = cuellos["resumen"]
    detalle = cuellos["detalle"]

    assert resumen == {"total": 3, "recursos": 1, "personal": 1, "dependencias": 1}
    recurso = next(item for item in detalle if item["tipo"] == "recurso")
    assert recurso["recurso"] == "horno"
    assert recurso["tareas"][:2] == ["Carrillera", "Costillar"]
    assert "capacidad disponible 1" in recurso["riesgo"]
    assert "retrasar el servicio" in recurso["consecuencia"]

    personal = next(item for item in detalle if item["tipo"] == "personal")
    assert "500 min" in personal["riesgo"]
    assert "450 min" in personal["riesgo"]

    dependencia = next(item for item in detalle if item["tipo"] == "dependencia")
    assert "Carrillera" in dependencia["titulo"]
    assert "Salsa" in " ".join(dependencia["tareas"])


def test_no_inventa_cuellos_si_faltan_datos_planificados(tmp_path):
    core = HostAICore(tmp_path)
    plan = core.produccion_real.crear_plan_manual("Plan sin datos")
    plan_id = plan["id"]
    tarea = core.produccion_real.anadir_tarea_manual(plan_id, "Vinagreta", prioridad=40, origen="escandallo_evento")
    core.produccion_real.anadir_fase_manual(plan_id, tarea["id"], "Mezclar", 15, tipo="preparacion", recurso="mesa_trabajo")

    panel = core.produccion_real.panel_produccion(plan_id)
    assert panel["cuellos_botella_previstos"] == {"resumen": {"total": 0, "recursos": 0, "personal": 0, "dependencias": 0}, "detalle": []}