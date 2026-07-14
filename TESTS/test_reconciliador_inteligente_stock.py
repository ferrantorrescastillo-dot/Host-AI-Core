from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Aceite oliva", "cantidad":10, "unidad":"l", "articulo_id":"ART-ACEITE", "ubicacion":"Seco", "coste_unitario":5}))
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Harina", "cantidad":20, "unidad":"kg", "articulo_id":"ART-HARINA", "ubicacion":"Seco", "coste_unitario":1}))
    inventario = [
        {"nombre":"Aceite oliva", "articulo_id":"ART-ACEITE", "cantidad":6, "unidad":"l"},
        {"nombre":"Harina", "articulo_id":"ART-HARINA", "cantidad":20, "unidad":"kg"},
        {"nombre":"Azúcar", "articulo_id":"ART-AZUCAR", "cantidad":4, "unidad":"kg"},
    ]
    r = core.orquestador.resolver(SolicitudHostAI("reconciliar_inteligente_stock", {"inventario_fisico": inventario, "tolerancia": 0.01}))
    assert r.ok is True
    assert r.datos["total_diferencias"] >= 2
    assert any(d["clave"] == "ART-ACEITE" and d["diferencia"] == -4 for d in r.datos["diferencias"])
    assert any(d["clave"] == "ART-AZUCAR" and d["diferencia"] == 4 for d in r.datos["diferencias"])
    print("TEST OK - Host AI 3.0.5.4 Reconciliador Inteligente de Stock")
    print("Diferencias:", r.datos["total_diferencias"])

if __name__ == "__main__": ejecutar_prueba()
