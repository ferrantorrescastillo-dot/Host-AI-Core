from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.orquestador_inteligente_52 import OrquestadorInteligente52


def main() -> int:
    o = OrquestadorInteligente52(ROOT)
    print("HOST AI 5.5.6E.3.3 - Flujo post-ficha")
    print("Usa el chat principal para la prueba completa. Este script verifica la carga del orquestador.")
    print(f"Versión: {o.VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
