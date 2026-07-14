from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Aceite oliva", "cantidad":12, "unidad":"l", "articulo_id":"ART-ACEITE", "ubicacion":"Seco", "coste_unitario":5}))
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Harina", "cantidad":25, "unidad":"kg", "articulo_id":"ART-HARINA", "ubicacion":"Seco", "coste_unitario":1}))
    core.orquestador.resolver(SolicitudHostAI("consumir_stock", {"nombre":"Aceite oliva", "cantidad":3, "unidad":"l", "articulo_id":"ART-ACEITE", "motivo":"salida producción"}))
    core.orquestador.resolver(SolicitudHostAI("consumir_stock", {"nombre":"Harina", "cantidad":2, "unidad":"kg", "articulo_id":"ART-HARINA", "motivo":"merma por rotura saco"}))
    r = core.orquestador.resolver(SolicitudHostAI("controlar_movimientos_stock", {}))
    assert r.ok is True
    assert r.datos["total_movimientos"] >= 4
    assert r.datos["total_entradas"] >= 2
    assert r.datos["total_salidas"] >= 2
    assert r.datos["total_mermas"] >= 1
    assert "ART-ACEITE" in r.datos["resumen_por_articulo"]
    print("TEST OK - Host AI 3.0.5.3 Control Inteligente de Entradas y Salidas")
    print("Movimientos:", r.datos["total_movimientos"])

if __name__ == "__main__": ejecutar_prueba()
