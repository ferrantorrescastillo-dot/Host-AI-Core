
from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.beta_conversacional_qa_506 import BetaConversacionalQA506


def main() -> None:
    qa = BetaConversacionalQA506(BASE_DIR)
    informe = qa.ejecutar()
    qa.imprimir_informe(informe)
    ruta = qa.guardar_informe(informe)
    print(f"\nInforme guardado en: {ruta}")


if __name__ == "__main__":
    main()
