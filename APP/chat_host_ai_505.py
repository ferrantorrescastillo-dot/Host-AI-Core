from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.integracion_nucleo_ia_505 import ChatHostAIIntegrado505


def main() -> None:
    chat = ChatHostAIIntegrado505(BASE_DIR)
    print("=" * 70)
    print("HOST AI 5.0.5 - CHAT CON CONFIRMACION DE RECEPCION")
    print("Escribe 'salir' para volver.")
    print("=" * 70)
    while True:
        texto = input("Tú: ").strip()
        if texto.lower() in {"salir", "volver", "0"}:
            print("Volviendo al bootloader.")
            break
        respuesta = chat.responder(texto)
        print("Host AI:", respuesta["mensaje"])


if __name__ == "__main__":
    main()
