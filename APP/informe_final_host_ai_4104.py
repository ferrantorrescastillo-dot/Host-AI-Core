from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.informe_final_host_ai_4104 import generar_informe_final_host_ai, formatear_informe_final_host_ai


if __name__ == "__main__":
    informe = generar_informe_final_host_ai(BASE_DIR)
    print(formatear_informe_final_host_ai(informe))
