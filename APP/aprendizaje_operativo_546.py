from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from SERVICIOS.aprendizaje_operativo_546 import aprender_operativa_546, formatear_aprendizaje_546


if __name__ == "__main__":
    print(formatear_aprendizaje_546(aprender_operativa_546()))
