from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def main() -> None:
    """Punto de entrada único y oficial de Host AI 6.0 — línea piloto."""
    from SERVICIOS.lanzador_piloto_01 import ejecutar_piloto_01

    ejecutar_piloto_01(BASE_DIR)


if __name__ == "__main__":
    main()
