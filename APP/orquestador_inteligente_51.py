from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.orquestador_inteligente_51 import OrquestadorInteligente51


def main() -> None:
    orquestador = OrquestadorInteligente51(BASE_DIR)
    print("=" * 70)
    print("HOST AI 5.1 - ORQUESTADOR INTELIGENTE")
    print("Escribe 'salir' para volver.")
    print("=" * 70)
    while True:
        texto = input("Tú: ").strip()
        if texto.lower() in {"salir", "volver", "0"}:
            print("Volviendo al bootloader.")
            break
        respuesta = orquestador.procesar(texto)
        print("Host AI:", respuesta["mensaje"])


if __name__ == "__main__":
    main()
