from pathlib import Path

from CORE.host_ai_core import HostAICore


def test_rr13_editar_necesidad_sincroniza_pedido_abierto(tmp_path: Path):
    core = HostAICore(tmp_path)
    necesidad = core.compras.registrar_necesidad(
        "Tomate triturado", 5, "kg", proveedor_preferente="Sardà", articulo_id="ART-TOMATE"
    )
    generado = core.compras.generar_pedidos_sugeridos()
    pedido_id = generado["pedidos_sugeridos"][0]["id"]

    core.compras.editar_necesidad(necesidad.id, cantidad=7, proveedor_preferente="Sardà Distribución")
    pedido = core.compras.obtener_pedido(pedido_id)

    assert pedido.proveedor == "Sardà Distribución"
    assert pedido.lineas[0].cantidad == 7
    assert pedido.lineas[0].necesidad_id == necesidad.id
    assert any(h["accion"] == "necesidad_sincronizada" for h in pedido.historial)

    segundo = core.compras.generar_pedidos_sugeridos()
    assert segundo["total_pedidos"] == 0
    assert segundo["pendientes_ya_vinculadas"] == 1
    assert segundo["pedidos_abiertos"] == 1


def test_rr13_cancelar_necesidad_retira_linea_de_pedido_editable(tmp_path: Path):
    core = HostAICore(tmp_path)
    tomate = core.compras.registrar_necesidad("Tomate", 5, "kg", proveedor_preferente="Makro")
    cebolla = core.compras.registrar_necesidad("Cebolla", 3, "kg", proveedor_preferente="Makro")
    generado = core.compras.generar_pedidos_sugeridos()
    pedido_id = generado["pedidos_sugeridos"][0]["id"]

    core.compras.cambiar_estado(tomate.id, "cancelada")
    pedido = core.compras.obtener_pedido(pedido_id)

    assert [l.necesidad_id for l in pedido.lineas] == [cebolla.id]
    assert any(h["accion"] == "necesidad_retirada" for h in pedido.historial)

    reiniciado = HostAICore(tmp_path)
    pedido_reiniciado = reiniciado.compras.obtener_pedido(pedido_id)
    assert len(pedido_reiniciado.lineas) == 1
    assert pedido_reiniciado.lineas[0].necesidad_id == cebolla.id
