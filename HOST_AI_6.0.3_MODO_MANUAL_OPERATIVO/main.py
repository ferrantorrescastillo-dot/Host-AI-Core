from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def main() -> None:
    """Punto de entrada único de Host AI Base 6.0.3."""
    from SERVICIOS.lanzador_host_ai_base_603 import ejecutar_host_ai

    ejecutar_host_ai(BASE_DIR)


if __name__ == "__main__":
    main()
