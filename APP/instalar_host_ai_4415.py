from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.instalador_host_ai_4415 import InstaladorHostAI4415


def main():
    instalador = InstaladorHostAI4415(ROOT)
    print("=== HOST AI 4.4.15 - INSTALADOR LOCAL ===")
    restaurante = input("Nombre restaurante (Enter = mantener/demo): ").strip() or None
    resultado = instalador.preparar_instalacion(restaurante=restaurante)
    print(resultado["lectura_host_ai"])
    informe = instalador.crear_informe_instalacion()
    print(informe["lectura_host_ai"])


if __name__ == "__main__":
    main()
