from __future__ import annotations

from SERVICIOS.clasificador_intenciones_503 import ClasificadorIntenciones503


def main() -> None:
    ejemplos = [
        "¿Cuánto arroz bomba tengo?",
        "¿Qué elaboraciones puedo adelantar hoy?",
        "Me falta aceite para el servicio.",
        "Cuál es el plato menos rentable.",
        "Han llegado 25 kg de arroz bomba de Makro a 2,15 €/kg.",
    ]
    clasificador = ClasificadorIntenciones503()
    print("=" * 70)
    print("HOST AI 5.0.7 - REFORZADOR CLASIFICADOR")
    print("=" * 70)
    for texto in ejemplos:
        r = clasificador.clasificar(texto)
        g = r["intencion_ganadora"]
        print(f"\nUsuario: {texto}")
        print(f"Intención: {g['intencion']} | confianza: {round(g['confianza'] * 100)}%")
        print(f"Motivo: {g['motivo']}")


if __name__ == "__main__":
    main()
