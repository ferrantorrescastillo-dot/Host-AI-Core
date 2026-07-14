from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.panel_estado_455 import PanelEstadoHostAI455


def main() -> None:
    PanelEstadoHostAI455(ROOT).imprimir_estado()


if __name__ == "__main__":
    main()
