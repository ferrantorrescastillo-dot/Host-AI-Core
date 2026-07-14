from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.conector_stock_real_553 import procesar_consulta_stock_real_553


if __name__ == "__main__":
    consulta = "¿Qué stock tienes de arroz bomba?"
    print(procesar_consulta_stock_real_553(consulta, BASE_DIR)["mensaje"])
