from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.conector_escandallos_real_555 import ConectorEscandallosReal555, formatear_escandallos_real_555


def main() -> int:
    termino = " ".join(sys.argv[1:]).strip() or "ensaladilla de gamba"
    resultado = ConectorEscandallosReal555(ROOT).consultar(termino)
    print(formatear_escandallos_real_555(resultado))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
