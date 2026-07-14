from pathlib import Path
import sys

# Permite ejecutar tanto:
#   python -m APP.bootloader_host_ai_502
# como, si alguien se equivoca:
#   python APP/bootloader_host_ai_502.py
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.bootloader_host_ai_502 import ejecutar_menu


if __name__ == "__main__":
    ejecutar_menu(BASE_DIR)
