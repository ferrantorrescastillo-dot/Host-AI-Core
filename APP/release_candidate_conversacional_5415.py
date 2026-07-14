from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.release_candidate_conversacional_5415 import ejecutar_release_candidate_5415, formatear_release_candidate_5415


if __name__ == "__main__":
    print(formatear_release_candidate_5415(ejecutar_release_candidate_5415(BASE_DIR)))
