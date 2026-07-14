from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.integracion_conversacional_datos_5414 import integrar_conversacion_datos_5414, formatear_integracion_5414


def main() -> None:
    evento = {"tipo": "boda", "personas": 150, "fecha": "sábado", "hora_servicio": "15:00", "menu": "paella", "lugar": "restaurante"}
    print(formatear_integracion_5414(integrar_conversacion_datos_5414(evento, base_dir=BASE_DIR)))


if __name__ == "__main__":
    main()
