from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.conector_escandallos_real_555 import procesar_consulta_escandallos_real_555

if __name__ == "__main__":
    texto = input("Consulta receta/escandallo: ").strip()
    print(procesar_consulta_escandallos_real_555(texto, BASE_DIR).get("mensaje"))
