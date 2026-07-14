from CORE.host_ai_core import HostAICore


def test_co1_costes_operativos_evento_e_historial(tmp_path):
    core = HostAICore(tmp_path)
    core.escandallos_inteligente.registrar_escandallo(
        "REC-CO1", "Receta CO1", 10,
        [{"nombre": "Tomate", "cantidad": 2, "unidad": "kg", "articulo_id": "ART-TOM", "coste_unitario": 0}],
    )
    core.costes_inteligente.registrar_precio("Tomate", 2.0, "kg", articulo_id="ART-TOM")
    evento = core.eventos.crear_evento("Evento CO1", "2026-10-22", 10)
    core.eventos.agregar_servicio(evento.id, "Comida", "comida", "13:00", 120)
    servicio = core.eventos.obtener(evento.id).servicios[0]
    core.eventos.agregar_pase(evento.id, servicio.id, "Entrante", "13:30", 30, ["REC-CO1"])

    d = core.costes_inteligente.calcular_coste_evento_operativo(
        evento.id,
        precio_venta_por_pax=20,
        horas_personal=10,
        coste_hora=15,
        costes_indirectos=25,
        otros_costes=10,
        coste_real_materia=50,
    )
    assert d["coste_materia_previsto"] == 4.0
    assert d["coste_mano_obra"] == 150.0
    assert d["coste_total_previsto"] == 189.0
    assert d["coste_total_real"] == 235.0
    assert d["desviacion"] == 46.0
    assert d["beneficio_real"] == -35.0
    assert d["margen_real_porcentaje"] == -17.5

    historial = core.costes_inteligente.listar_historial_costes_eventos(evento.id)
    assert len(historial) == 1
    assert historial[0]["evento"] == "Evento CO1"

    core2 = HostAICore(tmp_path)
    historial2 = core2.costes_inteligente.listar_historial_costes_eventos(evento.id)
    assert len(historial2) == 1
    assert historial2[0]["coste_total_real"] == 235.0
