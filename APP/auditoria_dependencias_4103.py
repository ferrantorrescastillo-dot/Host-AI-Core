from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.auditoria_dependencias_4103 import auditar_dependencias, formatear_auditoria_dependencias


if __name__ == "__main__":
    resultado = auditar_dependencias(BASE_DIR)
    print(formatear_auditoria_dependencias(resultado))
