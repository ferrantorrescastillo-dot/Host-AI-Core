from APP.consola import AppConsolaHostAI
from CORE.host_ai_core import HostAICore


def _inputs(monkeypatch, valores):
    it = iter(valores)
    monkeypatch.setattr("builtins.input", lambda _="": next(it))


def test_rr14_receta_activa_y_bloqueo_rentabilidad_vacia(tmp_path, monkeypatch, capsys):
    core = HostAICore(tmp_path)
    core.escandallos_inteligente.registrar_escandallo("REC-VACIA", "Receta vacía", 10, [])
    app = AppConsolaHostAI(core)

    _inputs(monkeypatch, ["receta vacía"])
    elegida = app._seleccionar_escandallo(False)
    assert elegida["receta_id"] == "REC-VACIA"
    assert app.ultimo_escandallo_id == "REC-VACIA"

    _inputs(monkeypatch, [""])
    activa = app._seleccionar_escandallo(False)
    assert activa["receta_id"] == "REC-VACIA"

    assert app._validar_escandallo_economico(activa) is False
    salida = capsys.readouterr().out
    assert "no tiene ingredientes" in salida.lower()


def test_rr14_precio_sobre_articulo_real_y_coste_correcto(tmp_path):
    core = HostAICore(tmp_path)
    core.escandallos_inteligente.registrar_escandallo(
        "REC-RR14", "Receta RR14", 10,
        [{"nombre": "Zanahoria", "cantidad": 2, "unidad": "kg", "articulo_id": "ART-ZAN"}],
    )
    core.costes_inteligente.registrar_precio("Zanahoria", 1.5, "kg", articulo_id="ART-ZAN", proveedor="Proveedor")
    d = core.costes_inteligente.calcular_coste_receta("REC-RR14", 10, 8)
    assert d["coste_total"] == 3.0
    assert d["coste_por_racion"] == 0.3
    assert d["food_cost_porcentaje"] == 3.75
