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
        ("¿Cuánto arroz bomba tengo?", "stock"),
        ("¿Cuánto queda de gambón?", "stock"),
        ("¿Tengo suficiente pollo?", "stock"),
        ("Mira si queda leche.", "stock"),
        ("Hay arroz suficiente para mañana?", "stock"),
        ("Qué producto está en rotura.", "stock"),
        ("Revisa existencias de pescado.", "stock"),
        ("Me falta aceite para el servicio.", "compras"),
        ("¿Qué artículos están por debajo del mínimo?", "compras"),
        ("¿A quién compro el gambón?", "compras"),
        ("¿Qué elaboraciones puedo adelantar hoy?", "produccion"),
        ("Prepara fondos y salsas para el sábado.", "produccion"),
        ("Quiero saber qué tareas hacen hoy los cocineros.", "produccion"),
        ("¿Qué puedo dejar hecho hoy para mañana?", "produccion"),
        ("Necesito un plan de trabajo de cocina.", "produccion"),
        ("Controla tiempos activos y pasivos.", "produccion"),
        ("Cuál es el plato menos rentable.", "rentabilidad"),
        ("Qué receta me hace perder dinero.", "rentabilidad"),
        ("Han llegado 25 kg de arroz bomba de Makro a 2,15 €/kg.", "recepcion_mercancia"),
    ]
    for texto, esperado in casos:
        assert_intencion(texto, esperado)
    print("TEST OK 5.0.7 Reforzador Clasificador")


if __name__ == "__main__":
    main()
