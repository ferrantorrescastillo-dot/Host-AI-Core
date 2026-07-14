from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    movimientos = [("entrada",20),("salida",5),("salida",4),("salida",6),("salida",5)]
    for tipo,cantidad in movimientos:
        core.orquestador.resolver(SolicitudHostAI("registrar_movimiento_stock_historico", {"movimiento": {"articulo_id":"ART-TOMATE", "nombre_articulo":"Tomate", "tipo": tipo, "cantidad": cantidad, "unidad":"kg", "proveedor_id":"PROV-HORT"}}))
    r = core.orquestador.resolver(SolicitudHostAI("predecir_roturas_stock", {"horizonte_dias": 14}))
    assert r.ok is True
    assert r.datos["total_articulos"] >= 1
    assert any(p["articulo_id"] == "ART-TOMATE" for p in r.datos["predicciones"])
    a = core.orquestador.resolver(SolicitudHostAI("predecir_rotura_articulo", {"articulo_id":"ART-TOMATE"}))
    assert a.ok is True
    print("TEST OK - Host AI 3.0.4.6 Predicción de Roturas de Stock")
    print("Predicciones:", r.datos["total_articulos"])

if __name__ == "__main__": ejecutar_prueba()
