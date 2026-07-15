from APP.consola_jornada_piloto_12 import ConsolaJornadaPiloto12
from APP.consola_produccion_guiada_piloto_13 import ConsolaProduccionGuiadaPiloto13


def _capturar(llamada):
    lineas = []
    llamada(lineas.append)
    return "\n".join(lineas)


def test_briefing_empieza_por_la_decision_operativa():
    jornada = {
        "fecha": "2026-07-16",
        "resumen": {"abiertas": 2, "muy_urgentes": 1, "hoy": 1, "esta_semana": 0},
        "recomendaciones": [
            {"titulo": "Empieza la carrillera", "motivo": "Necesita cocción larga."},
            {"titulo": "Corta las verduras", "motivo": "Puede adelantarse."},
        ],
        "alertas": [],
        "tiempos": {
            "activo_conocido_min": 60,
            "pasivo_conocido_min": 120,
            "tareas_sin_duracion": 0,
            "fin_estimado_por_trabajo_activo": None,
        },
        "briefing_apertura": {
            "incidencias": [],
            "alertas": [],
            "produccion_viva": {"siguiente_accion": "Empieza la carrillera", "progreso_promedio": 0, "tareas_pendientes": 2, "tareas_bloqueadas": 0},
            "produccion_priorizada": [],
            "productos_descongelar": [],
            "eventos_hoy": [{"hora": "13:30", "nombre": "Boda", "pax": 80}],
            "compras_criticas": [],
            "recepciones_previstas": [],
            "alergenos": {"estado": "sin_alertas"},
        },
    }
    consola = ConsolaJornadaPiloto12.__new__(ConsolaJornadaPiloto12)
    salida = _capturar(lambda imprimir: consola._mostrar_portada(jornada, imprimir))

    assert salida.index("QUÉ HAGO PRIMERO") < salida.index("RESUMEN DEL DÍA")
    assert salida.index("QUÉ PUEDE IMPEDIRME TRABAJAR") < salida.index("INFORMACIÓN DE APOYO")
    assert "> Empieza la carrillera" in salida
    assert "EVENTOS QUE REQUIEREN ATENCIÓN" in salida


def test_briefing_vacio_ofrece_siguiente_paso():
    briefing = {"eventos_hoy": []}
    salida = _capturar(lambda imprimir: ConsolaJornadaPiloto12._mostrar_eventos_atencion(briefing, imprimir))
    assert "No hay eventos hoy" in salida
    assert "Revisa el plan de mañana" in salida


def test_produccion_viva_prioriza_accion_y_oculta_detalle_tecnico():
    panel = {
        "plan": "Servicio del sábado",
        "avance": 20,
        "pendientes": 2,
        "en_curso": 0,
        "bloqueadas": 1,
        "alertas": [],
        "siguiente_accion": {"texto": "Resuelve el bloqueo de carrillera", "explicacion": "Faltan 3 kg de carrillera para continuar."},
        "tareas": [
            {"titulo": "Carrillera", "estado_texto": "Bloqueada", "estado_codigo": "incidencia", "prioridad_texto": "Muy urgente", "tiempo_restante_texto": "2 h", "bloqueo": "Faltan 3 kg de carrillera", "puede_iniciar": False, "responsable_texto": "Chef", "recurso_texto": "horno"},
            {"titulo": "Cortar verduras", "estado_texto": "Pendiente", "estado_codigo": "pendiente", "prioridad_texto": "Alta", "tiempo_restante_texto": "30 min", "bloqueo": "", "puede_iniciar": True, "responsable_texto": "Ayudante", "recurso_texto": "mesa"},
        ],
    }
    salida = _capturar(lambda imprimir: ConsolaProduccionGuiadaPiloto13._mostrar_panel(panel, imprimir))

    assert salida.index("QUÉ DEBO HACER AHORA") < salida.index("SIGUIENTE TRABAJO")
    assert "Faltan 3 kg de carrillera" in salida
    assert "puedes adelantar Cortar verduras" in salida
    assert "Responsable:" not in salida
    assert "Recurso:" not in salida
