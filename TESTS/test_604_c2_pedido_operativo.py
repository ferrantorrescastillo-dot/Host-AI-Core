from pathlib import Path
import pytest

from CORE.host_ai_core import HostAICore


def test_c2_pedido_operativo_ciclo_completo(tmp_path: Path):
    core = HostAICore(tmp_path)

    tomate = core.compras.registrar_necesidad(
        nombre="Tomate triturado", cantidad=5, unidad="kg",
        proveedor_preferente="Sardà", articulo_id="ART-TOMATE", familia="Conservas",
    )
    cebolla = core.compras.registrar_necesidad(
        nombre="Cebolla", cantidad=8, unidad="kg",
        proveedor_preferente="Sardà", articulo_id="ART-CEBOLLA", familia="Verduras",
    )

    generados = core.compras.generar_pedidos_sugeridos()
    assert generados["total_pedidos"] == 1
    pedido_id = generados["pedidos_sugeridos"][0]["id"]
    pedido = core.compras.obtener_pedido(pedido_id)
    assert pedido.estado == "borrador"
    assert len(pedido.lineas) == 2

    linea_tomate = next(l for l in pedido.lineas if l.nombre == "Tomate triturado")
    core.compras.editar_linea_pedido(pedido_id, linea_tomate.id, cantidad=6, precio_unitario=1.8)
    core.compras.agregar_linea_pedido(
        pedido_id, "Ajo", 2, "kg", articulo_id="ART-AJO",
        familia="Verduras", precio_unitario=3.0,
    )
    assert core.compras.obtener_pedido(pedido_id).importe_estimado() == 16.8

    core.compras.editar_pedido(pedido_id, observaciones="Entregar antes de las 10:00")
    core.compras.cambiar_estado_pedido(pedido_id, "preparado")
    core.compras.cambiar_estado_pedido(pedido_id, "enviado")

    recibido = core.compras.recibir_pedido(
        pedido_id, core.stock, ubicacion="seco",
        caducidades={linea_tomate.id: "2026-12-31"},
    )
    assert recibido["total_lineas"] == 3
    assert core.compras.obtener_pedido(pedido_id).estado == "recibido"
    assert core.compras.obtener(tomate.id).estado == "comprada"
    assert core.compras.obtener(cebolla.id).estado == "comprada"

    stock = core.stock.stock_actual()["items"]
    cantidades = {item["nombre"]: item["cantidad"] for item in stock}
    assert cantidades["Tomate triturado"] == 6
    assert cantidades["Cebolla"] == 8
    assert cantidades["Ajo"] == 2

    with pytest.raises(ValueError, match="ya fue recibido"):
        core.compras.recibir_pedido(pedido_id, core.stock)

    reiniciado = HostAICore(tmp_path)
    pedido_reiniciado = reiniciado.compras.obtener_pedido(pedido_id)
    assert pedido_reiniciado.estado == "recibido"
    assert pedido_reiniciado.observaciones == "Entregar antes de las 10:00"
    assert len(pedido_reiniciado.historial) >= 6
    assert reiniciado.stock.stock_actual()["total_items"] == 3


def test_c2_no_duplica_necesidades_en_pedidos_abiertos(tmp_path: Path):
    core = HostAICore(tmp_path)
    core.compras.registrar_necesidad("Harina", 20, "kg", proveedor_preferente="Makro")
    primero = core.compras.generar_pedidos_sugeridos()
    segundo = core.compras.generar_pedidos_sugeridos()
    assert primero["total_pedidos"] == 1
    assert segundo["total_pedidos"] == 0
