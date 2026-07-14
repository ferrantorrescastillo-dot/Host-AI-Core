from pathlib import Path
import sys
from datetime import date, timedelta
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Aceite oliva", "cantidad":2, "unidad":"l", "articulo_id":"ART-ACEITE", "ubicacion":"Seco", "coste_unitario":5.0}))
    core.orquestador.resolver(SolicitudHostAI("ajustar_minimo_stock", {"nombre":"Aceite oliva", "cantidad_minima":5, "articulo_id":"ART-ACEITE"}))
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Harina", "cantidad":60, "unidad":"kg", "articulo_id":"ART-HARINA", "ubicacion":"", "coste_unitario":1.0}))
    core.orquestador.resolver(SolicitudHostAI("ajustar_minimo_stock", {"nombre":"Harina", "cantidad_minima":10, "articulo_id":"ART-HARINA"}))
    r = core.orquestador.resolver(SolicitudHostAI("analizar_inteligente_stock", {"dias_sin_movimiento":0}))
    assert r.ok is True
    assert r.datos["total_articulos"] >= 2
    assert r.datos["articulos_stock_bajo"] >= 1
    assert r.datos["articulos_exceso_stock"] >= 1
    assert r.datos["valor_total_estimado"] >= 70
    print("TEST OK - Host AI 3.0.5.1 Analizador Inteligente de Stock")
    print("Artículos analizados:", r.datos["total_articulos"])

if __name__ == "__main__": ejecutar_prueba()
