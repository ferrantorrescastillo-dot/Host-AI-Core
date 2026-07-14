from pathlib import Path
from tempfile import TemporaryDirectory

from CORE.host_ai_core import HostAICore


def test_stock_persistencia_busqueda_y_correccion():
    with TemporaryDirectory() as tmp:
        base = Path(tmp)
        core = HostAICore(base)
        r1 = core.stock.registrar_entrada("Tomate", 5, "kg", familia="Verduras")
        r2 = core.stock.registrar_entrada("Aceite", 2, "L", familia="Despensa")
        assert r1["lote"]["nombre"] == "Tomate"
        assert core.stock.stock_actual()["total_items"] == 2

        reiniciado = HostAICore(base)
        actual = reiniciado.stock.stock_actual()
        assert actual["total_items"] == 2
        assert any(x["nombre"] == "Tomate" for x in actual["items"])

        ultima = reiniciado.stock.ultima_entrada()
        assert ultima["lote"]["nombre"] == "Aceite"
        corregido = reiniciado.stock.corregir_ultima_entrada()
        assert corregido["ok"] is True
        assert reiniciado.stock.stock_actual()["total_items"] == 1

        reiniciado2 = HostAICore(base)
        assert reiniciado2.stock.stock_actual()["total_items"] == 1
        assert reiniciado2.stock.stock_actual()["items"][0]["nombre"] == "Tomate"
