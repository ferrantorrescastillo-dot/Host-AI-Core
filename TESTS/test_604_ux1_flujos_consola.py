from APP.consola import AppConsolaHostAI
from CORE.host_ai_core import HostAICore


def _inputs(monkeypatch, valores):
    it = iter(valores)
    monkeypatch.setattr("builtins.input", lambda _="": next(it))


def test_ux1_si_no_repregunta(monkeypatch, capsys):
    _inputs(monkeypatch, ["patata", "s"])
    assert AppConsolaHostAI._preguntar_si_no("¿Continuar?", por_defecto=False) is True
    assert "Responde 's'" in capsys.readouterr().out


def test_ux1_cancelar_necesidad_con_enter(tmp_path, monkeypatch, capsys):
    core = HostAICore(tmp_path)
    core.compras.registrar_necesidad("Tomate", 2, "kg", "Sardà")
    app = AppConsolaHostAI(core)
    _inputs(monkeypatch, [""])
    assert app._seleccionar_necesidad_compra() is None
    assert "Operación cancelada" in capsys.readouterr().out


def test_ux1_auto_selecciona_escandallo_unico(tmp_path, monkeypatch, capsys):
    core = HostAICore(tmp_path)
    core.escandallos_inteligente.registrar_escandallo("REC-UNO", "Receta única", 4, [])
    app = AppConsolaHostAI(core)
    _inputs(monkeypatch, ["receta única"])
    elegido = app._seleccionar_escandallo()
    assert elegido["receta_id"] == "REC-UNO"
    assert "seleccionado automáticamente" in capsys.readouterr().out


def test_ux1_busqueda_articulo_vacia_cancela(tmp_path, monkeypatch, capsys):
    app = AppConsolaHostAI(HostAICore(tmp_path))
    _inputs(monkeypatch, [""])
    assert app._seleccionar_articulo_stock() is None
    assert "cancelada" in capsys.readouterr().out.lower()
