from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI


def _registrar_escandallo_base(core, receta_id="REC-PLATO", nombre="Plato sprint"):
    core.escandallos_inteligente.registrar_escandallo(
        receta_id,
        nombre,
        10,
        [
            {
                "nombre": "Tomate",
                "cantidad": 2,
                "unidad": "kg",
                "articulo_id": f"ART-{receta_id}",
                "coste_unitario": 0,
            }
        ],
    )
    core.costes_inteligente.registrar_precio(
        "Tomate",
        2.0,
        "kg",
        articulo_id=f"ART-{receta_id}",
    )


def _crear_evento_con_pase(core, pax=10, recetas=None):
    evento = core.eventos.crear_evento("Evento Sprint", "2026-10-22", pax)
    core.eventos.agregar_servicio(evento.id, "Comida", "comida", "13:00", 120)
    servicio = core.eventos.obtener(evento.id).servicios[0]
    core.eventos.agregar_pase(evento.id, servicio.id, "Principal", "13:30", 30, recetas or [])
    pase = core.eventos.obtener(evento.id).servicios[0].pases[0]
    return evento, servicio, pase


def test_evento_agregar_plato_referencia_escandallo_pax_evento(tmp_path):
    core = HostAICore(tmp_path)
    _registrar_escandallo_base(core, "REC-PAX", "Plato Pax")
    evento, servicio, pase = _crear_evento_con_pase(core, pax=12)

    core.eventos.agregar_plato(evento.id, servicio.id, pase.id, "REC-PAX")

    pase_actualizado = core.eventos.obtener(evento.id).servicios[0].pases[0]
    assert len(pase_actualizado.platos) == 1
    assert pase_actualizado.platos[0]["escandallo_id"] == "REC-PAX"
    assert pase_actualizado.platos[0]["raciones"] == 12
    assert "REC-PAX" in pase_actualizado.recetas


def test_evento_agregar_plato_raciones_manual(tmp_path):
    core = HostAICore(tmp_path)
    _registrar_escandallo_base(core, "REC-MANUAL", "Plato Manual")
    evento, servicio, pase = _crear_evento_con_pase(core, pax=20)

    core.eventos.agregar_plato(
        evento.id,
        servicio.id,
        pase.id,
        "REC-MANUAL",
        usar_pax_evento=False,
        raciones=5,
    )

    plato = core.eventos.obtener(evento.id).servicios[0].pases[0].platos[0]
    assert plato["usar_pax_evento"] is False
    assert plato["raciones"] == 5


def test_evento_agregar_plato_falla_si_escandallo_no_existe(tmp_path):
    core = HostAICore(tmp_path)
    evento, servicio, pase = _crear_evento_con_pase(core)

    try:
        core.eventos.agregar_plato(evento.id, servicio.id, pase.id, "REC-INEXISTENTE")
        assert False, "Se esperaba ValueError por escandallo inexistente"
    except ValueError as exc:
        assert "no existe" in str(exc).lower() or "disponible" in str(exc).lower()


def test_evento_agregar_plato_falla_si_raciones_invalidas(tmp_path):
    core = HostAICore(tmp_path)
    _registrar_escandallo_base(core, "REC-RACIONES", "Plato Raciones")
    evento, servicio, pase = _crear_evento_con_pase(core, pax=10)

    try:
        core.eventos.agregar_plato(
            evento.id,
            servicio.id,
            pase.id,
            "REC-RACIONES",
            usar_pax_evento=False,
            raciones=0,
        )
        assert False, "Se esperaba ValueError por raciones inválidas"
    except ValueError as exc:
        assert "raciones" in str(exc).lower()


def test_evento_listar_platos_legacy_desde_recetas(tmp_path):
    core = HostAICore(tmp_path)
    _registrar_escandallo_base(core, "REC-LEGACY", "Plato Legacy")
    evento, servicio, pase = _crear_evento_con_pase(core, pax=9, recetas=["REC-LEGACY"])

    platos = core.eventos.listar_platos_pase(evento.id, servicio.id, pase.id)

    assert len(platos) == 1
    assert platos[0]["legacy"] is True
    assert platos[0]["escandallo_id"] == "REC-LEGACY"
    assert platos[0]["raciones"] == 9


def test_escandallos_evento_prioriza_platos_sobre_recetas_legacy(tmp_path):
    core = HostAICore(tmp_path)
    _registrar_escandallo_base(core, "REC-PLATO", "Plato Nuevo")
    _registrar_escandallo_base(core, "REC-LEGACY", "Plato Legacy")
    evento, servicio, pase = _crear_evento_con_pase(core, pax=10, recetas=["REC-LEGACY"])
    core.eventos.agregar_plato(evento.id, servicio.id, pase.id, "REC-PLATO", usar_pax_evento=False, raciones=3)

    calculo = core.escandallos_inteligente.calcular_necesidades_evento(core.eventos.obtener(evento.id).to_dict())

    recetas = [r["receta_id"] for r in calculo["recetas_calculadas"]]
    assert recetas == ["REC-PLATO"]
    assert calculo["recetas_calculadas"][0]["raciones_calculadas"] == 3


def test_escandallos_evento_compatibilidad_recetas_legacy(tmp_path):
    core = HostAICore(tmp_path)
    _registrar_escandallo_base(core, "REC-LEGACY", "Plato Legacy")
    evento, _, _ = _crear_evento_con_pase(core, pax=8, recetas=["REC-LEGACY"])

    calculo = core.escandallos_inteligente.calcular_necesidades_evento(core.eventos.obtener(evento.id).to_dict())

    assert calculo["recetas_calculadas"][0]["receta_id"] == "REC-LEGACY"
    assert calculo["recetas_calculadas"][0]["raciones_calculadas"] == 8


def test_costes_evento_calcula_desde_platos_con_raciones_propias(tmp_path):
    core = HostAICore(tmp_path)
    _registrar_escandallo_base(core, "REC-COSTE", "Plato Coste")
    evento, servicio, pase = _crear_evento_con_pase(core, pax=20)
    core.eventos.agregar_plato(evento.id, servicio.id, pase.id, "REC-COSTE", usar_pax_evento=False, raciones=5)

    coste = core.costes_inteligente.calcular_coste_evento(evento.id, precio_venta_por_pax=10)

    assert len(coste["recetas"]) == 1
    assert coste["recetas"][0]["receta_id"] == "REC-COSTE"
    assert coste["recetas"][0]["raciones"] == 5
    assert coste["coste_materia_prima"] == 2.0


def test_orquestador_agregar_plato_evento(tmp_path):
    core = HostAICore(tmp_path)
    _registrar_escandallo_base(core, "REC-ORQ", "Plato Orquestador")
    evento, servicio, pase = _crear_evento_con_pase(core, pax=11)

    respuesta = core.orquestador.resolver(SolicitudHostAI("agregar_plato_evento", {
        "evento_id": evento.id,
        "servicio_id": servicio.id,
        "pase_id": pase.id,
        "escandallo_id": "REC-ORQ",
        "usar_pax_evento": True,
    }))

    assert respuesta.ok is True
    pase_datos = respuesta.datos["evento"]["servicios"][0]["pases"][0]
    assert len(pase_datos["platos"]) == 1
    assert pase_datos["platos"][0]["escandallo_id"] == "REC-ORQ"


def test_linea_temporal_y_resumen_reflejan_platos(tmp_path):
    core = HostAICore(tmp_path)
    _registrar_escandallo_base(core, "REC-LIN", "Plato Línea")
    evento, servicio, pase = _crear_evento_con_pase(core, pax=10)
    core.eventos.agregar_plato(evento.id, servicio.id, pase.id, "REC-LIN")

    linea = core.eventos.construir_linea_temporal(evento.id)
    resumen = core.eventos.resumen_ejecutivo(evento.id)

    assert linea["totales"]["platos_en_pases"] == 1
    pase_linea = [item for item in linea["linea_temporal"] if item["tipo"] == "pase"][0]
    assert pase_linea["platos"][0]["escandallo_id"] == "REC-LIN"
    assert resumen["totales"]["recetas"] == 1