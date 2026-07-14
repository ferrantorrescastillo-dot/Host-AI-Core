from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.conector_proveedores_real_554 import procesar_consulta_proveedores_real_554


if __name__ == "__main__":
    consulta = "¿Qué proveedores venden arroz bomba?"
    print(procesar_consulta_proveedores_real_554(consulta, BASE_DIR)["mensaje"])
