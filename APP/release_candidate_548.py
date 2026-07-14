from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from SERVICIOS.release_candidate_548 import ejecutar_release_candidate_548, formatear_release_candidate_548


if __name__ == "__main__":
    print(formatear_release_candidate_548(ejecutar_release_candidate_548()))
