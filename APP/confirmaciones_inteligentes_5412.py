from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.confirmaciones_inteligentes_5412 import interpretar_confirmacion_contextual_5412

if __name__ == "__main__":
    contexto = {"activo": True, "estado_conversacion": "esperando_confirmacion_especifica", "accion_seleccionada": {"codigo": "compras", "nombre": "Preparar compras necesarias"}, "confirmaciones": {"acciones_con_confirmacion": [{"codigo": "compras", "nombre": "Preparar compras necesarias"}]}}
    for frase in ["adelante", "aplica solo compras", "vuelve atrás"]:
        print(frase, "->", interpretar_confirmacion_contextual_5412(frase, contexto))
