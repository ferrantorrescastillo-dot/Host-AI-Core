from SERVICIOS.clasificador_intenciones_503 import ClasificadorIntenciones503


def main():
    c = ClasificadorIntenciones503()

    r1 = c.clasificar("Han llegado 25 kg de arroz bomba de Makro a 2,15 €/kg.")
    assert r1["intencion_ganadora"]["intencion"] == "recepcion_mercancia", r1
    assert r1["intencion_ganadora"]["confianza"] >= 0.80, r1

    r2 = c.clasificar("Necesito preparar una boda para 180 personas el sábado.")
    assert r2["intencion_ganadora"]["intencion"] in {"evento", "produccion"}, r2

    r3 = c.clasificar("¿Cuál es el plato que menos beneficio me deja?")
    assert r3["intencion_ganadora"]["intencion"] == "rentabilidad", r3

    r4 = c.clasificar("¿Qué tengo que comprar para mañana?")
    assert r4["intencion_ganadora"]["intencion"] == "compras", r4

    print("TEST OK 5.0.3 Clasificador Inteligente de Intenciones")


if __name__ == "__main__":
    main()
