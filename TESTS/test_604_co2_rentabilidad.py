from CORE.host_ai_core import HostAICore


def test_co2_rentabilidad_simulacion_rankings_e_historial(tmp_path):
    core=HostAICore(tmp_path)
    core.escandallos_inteligente.registrar_escandallo("REC-CO2","Receta CO2",10,[{"nombre":"Tomate","cantidad":2,"unidad":"kg","articulo_id":"ART-TOM"}])
    core.costes_inteligente.registrar_precio("Tomate",2.0,"kg",articulo_id="ART-TOM")
    evento=core.eventos.crear_evento("Evento CO2","2026-10-22",10,cliente="Cliente A")
    core.eventos.agregar_servicio(evento.id,"Comida","comida","13:00",120)
    servicio=core.eventos.obtener(evento.id).servicios[0]
    core.eventos.agregar_pase(evento.id,servicio.id,"Pase","13:30",30,["REC-CO2"])
    core.costes_inteligente.calcular_coste_receta("REC-CO2",10,20)
    core.costes_inteligente.calcular_coste_evento_operativo(evento.id,20,4,10,10,0,5)
    d=core.costes_inteligente.analizar_rentabilidad_evento(evento.id)
    assert d["beneficio"]==145.0
    assert d["margen_porcentaje"]==72.5
    assert d["cliente"]=="Cliente A"
    sim=core.costes_inteligente.simular_rentabilidad_evento(evento.id,25,20,10,0)
    assert sim["venta_total"]==500.0
    assert sim["beneficio"]>d["beneficio"]
    rankings=core.costes_inteligente.rankings_rentabilidad()
    assert rankings["eventos"][0]["evento"]=="Evento CO2"
    assert rankings["clientes"][0]["cliente"]=="Cliente A"
    resumen=core.costes_inteligente.resumen_rentabilidad_global()
    assert resumen["eventos_analizados"]==1
    core2=HostAICore(tmp_path)
    assert len(core2.costes_inteligente.historial_rentabilidad)==1
