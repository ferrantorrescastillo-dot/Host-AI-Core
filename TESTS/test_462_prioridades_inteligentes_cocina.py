from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from SERVICIOS.prioridades_inteligentes_cocina_462 import MotorPrioridadesInteligentesCocina462

def main():
    datos = [
        {"nombre":"Vinagreta", "tiempo_activo_min":10, "prioridad":"normal"},
        {"nombre":"Fondo oscuro", "tiempo_activo_min":45, "tiempo_pasivo_min":240, "prioridad":"alta"},
        {"nombre":"Carrilleras", "tiempo_activo_min":110, "tiempo_pasivo_min":180, "prioridad":"alta", "dependencias":["Fondo oscuro"]},
    ]
    r = MotorPrioridadesInteligentesCocina462().ordenar_prioridades(datos)
    assert r["version"] == "4.6.2"
    nombres = [x["nombre"] for x in r["prioridades"]]
    assert nombres.index("Fondo oscuro") < nombres.index("Carrilleras")
    assert nombres.index("Fondo oscuro") < nombres.index("Vinagreta")
    print("TEST OK - Host AI 4.6.2 Prioridades inteligentes de cocina")
if __name__ == "__main__": main()
