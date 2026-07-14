from SERVICIOS.clasificador_intenciones_503 import ClasificadorIntenciones503


def assert_intencion(texto, esperado):
    c = ClasificadorIntenciones503()
    r = c.clasificar(texto)
    obtenido = r["intencion_ganadora"]["intencion"]
    confianza = r["intencion_ganadora"]["confianza"]
    assert obtenido == esperado, f"{texto!r}: esperado {esperado}, obtenido {obtenido}"
    assert confianza >= 0.55, f"{texto!r}: confianza baja {confianza}"


def main():
    casos = [
        ("Prepara la compra de hoy.", "compras"),
        ("¿Qué falta comprar para el evento?", "compras"),
        ("Tengo que pedir tomate.", "compras"),
        ("Revisa si hay que comprar pescado.", "compras"),
        ("¿Cuánto tengo que pedir de arroz?", "compras"),
        ("Simula subir la paella a 48 euros.", "rentabilidad"),
        ("Controla mermas de producción.", "rentabilidad"),
        ("Comparar coste entre proveedores.", "rentabilidad"),
        ("Informe financiero inteligente.", "rentabilidad"),
    ]
    for texto, esperado in casos:
        assert_intencion(texto, esperado)
    print("TEST OK 5.0.8 Afinador Compras + Rentabilidad")


if __name__ == "__main__":
    main()
