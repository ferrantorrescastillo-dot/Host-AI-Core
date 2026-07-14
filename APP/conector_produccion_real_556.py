from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.conector_produccion_real_556 import procesar_consulta_produccion_real_556

if __name__ == "__main__":
    texto = input("Petición de producción: ").strip()
    print(procesar_consulta_produccion_real_556(texto, BASE_DIR).get("mensaje"))
