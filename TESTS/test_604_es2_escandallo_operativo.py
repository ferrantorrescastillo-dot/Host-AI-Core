from CORE.host_ai_core import HostAICore


def test_es2_costes_simulacion_e_historial(tmp_path):
    core = HostAICore(tmp_path)
    core.escandallos_inteligente.registrar_escandallo(
        "REC-ES2", "Receta ES2", 10,
        [{"nombre": "Tomate", "cantidad": 2, "unidad": "kg", "articulo_id": "ART-TOM", "coste_unitario": 0}],
    )
    core.costes_inteligente.registrar_precio("Tomate", 2.0, "kg", articulo_id="ART-TOM", proveedor="Proveedor A")

    calculo = core.costes_inteligente.calcular_coste_receta("REC-ES2", 10, 10)
    assert calculo["coste_total"] == 4.0
    assert calculo["coste_por_racion"] == 0.4
    assert calculo["food_cost_porcentaje"] == 4.0
    assert calculo["margen_bruto"] == 96.0
    assert calculo["lineas"][0]["proveedor"] == "Proveedor A"

    sim = core.costes_inteligente.simular_precio_linea_receta("REC-ES2", 10, "Tomate", 3.0, 10)
    assert sim["despues"]["coste_total"] == 6.0
    assert sim["impacto"]["coste_total"] == 2.0

    historial = core.costes_inteligente.listar_historial_escandallo("REC-ES2")
    assert historial
    assert historial[0]["receta_id"] == "REC-ES2"

    core2 = HostAICore(tmp_path)
    historial2 = core2.costes_inteligente.listar_historial_escandallo("REC-ES2")
    assert historial2
