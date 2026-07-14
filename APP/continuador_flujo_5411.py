from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.continuador_flujo_5411 import interpretar_seleccion


def main() -> None:
    acciones = [
        {"codigo": "EVENTO_CREAR", "nombre": "Crear o localizar evento"},
        {"codigo": "MENU_ASOCIAR", "nombre": "Asociar menú del evento"},
        {"codigo": "COMPRAS_PREPARAR", "nombre": "Preparar compras necesarias"},
    ]
    print("HOST AI 5.4.11 - CONTINUADOR INTELIGENTE DEL FLUJO")
    for ejemplo in ("1", "asociar menú", "3"):
        print(ejemplo, "->", interpretar_seleccion(ejemplo, acciones).get("accion", {}).get("nombre"))


if __name__ == "__main__":
    main()
