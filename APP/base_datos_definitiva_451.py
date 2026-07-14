from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.gestor_base_datos_definitiva_451 import GestorBaseDatosDefinitiva451


def main():
    gestor = GestorBaseDatosDefinitiva451(ROOT)
    print("=== HOST AI 4.5.1 - BASE DE DATOS DEFINITIVA ===")
    resultado = gestor.inicializar()
    print(resultado["lectura_host_ai"])
    migracion = gestor.migrar_json_basico()
    print(migracion["lectura_host_ai"])
    estado = gestor.estado()
    print("Tablas:", ", ".join(estado.get("tablas", [])))


if __name__ == "__main__":
    main()
