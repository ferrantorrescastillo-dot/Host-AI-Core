from pathlib import Path

from APP.consola import AppConsolaHostAI
from CORE.host_ai_core import HostAICore


def _crear_pedido(core: HostAICore):
    necesidad = core.compras.registrar_necesidad(
        "Arroz bomba", 5, "kg", proveedor_preferente="Makro", articulo_id="ART-ARROZ"
    )
    generado = core.compras.generar_pedidos_sugeridos()
    pedido_id = generado["pedidos_sugeridos"][0]["id"]
    return necesidad, pedido_id


def test_rr161b_resumen_distingue_pendientes_libres_y_vinculadas(tmp_path: Path):
    core = HostAICore(tmp_path)
    core.compras.registrar_necesidad("Arroz bomba", 5, "kg", proveedor_preferente="Makro")
    core.compras.registrar_necesidad("Tomate", 3, "kg", proveedor_preferente="Sardà")
    core.compras.generar_pedidos_sugeridos()
    core.compras.registrar_necesidad("Aceite", 2, "L", proveedor_preferente="Makro")

    resumen = core.compras.resumen_necesidades()

    assert resumen["pendientes_sin_pedido"] == 1
    assert resumen["vinculadas_a_pedido"] == 2
    assert resumen["total_pendientes"] == 3


def test_rr161b_recepcion_devuelve_datos_planos_y_guarda_precio(tmp_path: Path):
    core = HostAICore(tmp_path)
    necesidad, pedido_id = _crear_pedido(core)
    pedido = core.compras.obtener_pedido(pedido_id)
    linea = pedido.lineas[0]

    resultado = core.compras.recibir_pedido(
        pedido_id,
        core.stock,
        ubicacion="seco",
        costes={linea.id: 1.65},
    )

    entrada = resultado["entradas_stock"][0]
    assert entrada["nombre"] == "Arroz bomba"
    assert entrada["cantidad"] == 5
    assert entrada["unidad"] == "kg"
    assert entrada["ubicacion"] == "seco"
    assert entrada["coste_unitario"] == 1.65
    assert entrada["importe"] == 8.25
    assert entrada["lote_id"].startswith("LOTE-")
    assert core.compras.obtener_pedido(pedido_id).lineas[0].precio_unitario == 1.65
    assert core.compras.obtener(necesidad.id).estado == "comprada"


def test_rr161b_consola_propone_ultimo_coste_y_muestra_resumen(monkeypatch, capsys, tmp_path: Path):
    core = HostAICore(tmp_path)
    core.stock.registrar_entrada(
        "Arroz bomba", 2, "kg", articulo_id="ART-ARROZ", proveedor="Makro",
        ubicacion="seco", coste_unitario=1.65,
    )
    _, pedido_id = _crear_pedido(core)
    app = AppConsolaHostAI(core)
    app.ultimo_pedido_compra_id = pedido_id

    respuestas = iter([
        "",      # usar pedido activo
        "s",     # recibir pedido en borrador igualmente
        "seco",  # ubicación
        "",      # caducidad
        "",      # aceptar último coste 1.65
        "s",     # confirmar recepción
    ])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(respuestas))

    app._recibir_pedido_compra()
    salida = capsys.readouterr().out

    assert "AVISO: este pedido todavía está en borrador" in salida
    assert "RESUMEN DE RECEPCIÓN" in salida
    assert "Arroz bomba: +5 kg" in salida
    assert "Coste: 1.65 €/kg" in salida
    assert "Importe: 8.25 €" in salida
    assert "Pedido: RECIBIDO" in salida
