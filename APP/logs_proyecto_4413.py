from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.registro_logs_proyecto_4413 import RegistroLogsProyecto4413


def main() -> None:
    logger = RegistroLogsProyecto4413(BASE_DIR)
    resumen = logger.resumen()
    print("\n" + "=" * 60)
    print("HOST AI LOG CENTER - 4.4.13")
    print("=" * 60)
    print(resumen["lectura_host_ai"])
    print(f"Archivo: {resumen['log_path']}")
    print("\nÚltimas ejecuciones:")
    for item in logger.listar(limite=20):
        estado = "OK" if item.get("ok") else "FAIL"
        print(f"[{estado}] {item.get('fecha')} | {item.get('modulo')} | {item.get('accion')} | {item.get('duracion_segundos')}s")
        if item.get("errores"):
            print("  Errores:", ", ".join(item.get("errores", [])))


if __name__ == "__main__":
    main()
