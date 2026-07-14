from SERVICIOS.acciones_automaticas_seguras_492 import clasificar_accion, preparar_accion_segura, preparar_lote_acciones


def main():
    segura = preparar_accion_segura("crear_borrador_pedido", {"proveedor": "Makro"})
    assert segura["estado"] == "lista_para_ejecutar"
    pendiente = preparar_accion_segura("actualizar_stock", {"articulo": "Arroz"})
    assert pendiente["estado"] == "pendiente_confirmacion"
    confirmada = preparar_accion_segura("actualizar_stock", {"articulo": "Arroz"}, confirmado=True)
    assert confirmada["estado"] == "confirmada"
    assert clasificar_accion("accion_rara")["permitida"] is False
    lote = preparar_lote_acciones([{"accion": "crear_informe"}, {"accion": "modificar_precio"}])
    assert lote["total"] == 2
    assert len(lote["pendientes_confirmacion"]) == 1
    print("TEST OK 4.9.2 Acciones automáticas seguras")


if __name__ == "__main__":
    main()
