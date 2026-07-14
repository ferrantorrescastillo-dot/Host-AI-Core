from SERVICIOS.acciones_automaticas_seguras_492 import preparar_lote_acciones


def main():
    acciones = [
        {"accion": "crear_borrador_pedido", "datos": {"proveedor": "Makro"}},
        {"accion": "actualizar_stock", "datos": {"articulo": "Arroz", "cantidad": 10}},
        {"accion": "cerrar_recepcion", "confirmado": True},
    ]
    resultado = preparar_lote_acciones(acciones)
    print("Acciones listas:", len(resultado["listas"]))
    print("Pendientes confirmación:", len(resultado["pendientes_confirmacion"]))
    print("Bloqueadas:", len(resultado["bloqueadas"]))


if __name__ == "__main__":
    main()
