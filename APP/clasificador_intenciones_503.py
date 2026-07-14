from __future__ import annotations

from SERVICIOS.clasificador_intenciones_503 import ClasificadorIntenciones503


def main() -> None:
    clasificador = ClasificadorIntenciones503()
    print("HOST AI 5.0.3 - Clasificador Inteligente de Intenciones")
    print("Escribe una frase. 'salir' para terminar.")
    while True:
        texto = input("Tú: ").strip()
        if texto.lower() in {"salir", "0", "volver"}:
            break
        resultado = clasificador.clasificar(texto)
        print(resultado["lectura_host_ai"])
        print("Ranking:")
        for item in resultado["ranking"][:5]:
            print(f"- {item['intencion']}: {round(item['confianza'] * 100)}% | {item['accion_sugerida']}")


if __name__ == "__main__":
    main()
