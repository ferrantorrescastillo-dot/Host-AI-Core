from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from SERVICIOS.conversacion_natural_5413 import resolver_referencia_natural_5413
if __name__ == "__main__":
    acciones=[{"codigo":"evento","nombre":"Crear evento"},{"codigo":"menu","nombre":"Asociar menú"},{"codigo":"compras","nombre":"Preparar compras"}]
    contexto={"confirmaciones":{"acciones_con_confirmacion":acciones},"accion_seleccionada":acciones[0]}
    for frase in ["la segunda", "mejor la otra", "esa opción", "qué queda pendiente"]:
        print(frase, "->", resolver_referencia_natural_5413(frase, contexto))
