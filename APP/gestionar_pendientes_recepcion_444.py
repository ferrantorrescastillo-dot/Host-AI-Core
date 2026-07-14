from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.gestor_pendientes_recepcion_444 import GestorPendientesRecepcion444


def main():
    crear = "--crear" in sys.argv

    ruta_recepcion = ROOT / "DATOS" / "db" / "recepcion_mercancia_validada_4_4_2.json"
    ruta_articulos = ROOT / "DATOS" / "db" / "articulos.json"
    ruta_json = ROOT / "DATOS" / "db" / "pendientes_recepcion_4_4_4.json"
    ruta_txt = ROOT / "DATOS" / "db" / "pendientes_recepcion_4_4_4.txt"

    gestor = GestorPendientesRecepcion444(str(ruta_recepcion), str(ruta_articulos))
    resultado = gestor.exportar(crear=crear, ruta_json=str(ruta_json), ruta_txt=str(ruta_txt))

    print("HOST AI 4.4.4 - Pendientes de Recepción")
    print("Modo:", "CREAR ARTÍCULOS" if crear else "SOLO REVISIÓN")
    print("JSON generado:", ruta_json)
    print("TXT generado:", ruta_txt)
    print("Pendientes:", resultado.total_pendientes)
    print("Creados:", resultado.creados)
    print("No creados:", resultado.no_creados)
    print("Estado:", resultado.estado)


if __name__ == "__main__":
    main()
