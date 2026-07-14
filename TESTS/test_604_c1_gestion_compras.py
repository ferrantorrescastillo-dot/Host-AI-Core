from pathlib import Path

from CORE.host_ai_core import HostAICore


def test_c1_gestion_compras_persistencia_y_estados(tmp_path: Path):
    core = HostAICore(tmp_path)

    tomate = core.compras.registrar_necesidad(
        nombre="Tomate triturado",
        cantidad=5,
        unidad="kg",
        proveedor_preferente="Sardà",
        prioridad=80,
        articulo_id="ART-TOMATE",
    )
    aceite = core.compras.registrar_necesidad(
        nombre="Aceite de oliva",
        cantidad=10,
        unidad="L",
        proveedor_preferente="Makro",
        prioridad=95,
        articulo_id="ART-ACEITE",
    )

    core.compras.editar_necesidad(tomate.id, cantidad=7, motivo="Producción fin de semana")
    core.compras.cambiar_estado(aceite.id, "comprada")

    pendientes = core.compras.listar_necesidades()
    assert len(pendientes) == 1
    assert pendientes[0]["id"] == tomate.id
    assert pendientes[0]["cantidad"] == 7

    pedidos = core.compras.generar_pedidos_sugeridos()
    assert pedidos["total_pedidos"] == 1
    assert pedidos["total_necesidades"] == 1
    assert pedidos["pedidos_sugeridos"][0]["proveedor"] == "Sardà"

    reiniciado = HostAICore(tmp_path)
    assert reiniciado.compras.obtener(tomate.id).cantidad == 7
    assert reiniciado.compras.obtener(tomate.id).motivo == "Producción fin de semana"
    assert reiniciado.compras.obtener(aceite.id).estado == "comprada"

    reiniciado.compras.cambiar_estado(aceite.id, "pendiente")
    assert len(reiniciado.compras.listar_necesidades()) == 2
    assert reiniciado.compras.eliminar_necesidad(tomate.id) is True
    assert reiniciado.compras.obtener(tomate.id) is None
