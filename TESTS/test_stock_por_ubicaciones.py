from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI


def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Aceite oliva", "cantidad":10, "unidad":"l", "articulo_id":"ART-ACEITE", "ubicacion":"Seco", "coste_unitario":5}))
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Tomate", "cantidad":8, "unidad":"kg", "articulo_id":"ART-TOMATE", "ubicacion":"Cámara", "coste_unitario":2}))
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Harina", "cantidad":20, "unidad":"kg", "articulo_id":"ART-HARINA", "ubicacion":"", "coste_unitario":1}))
    r = core.orquestador.resolver(SolicitudHostAI("analizar_stock_ubicaciones", {}))
    assert r.ok, r.mensaje
    assert r.datos["total_ubicaciones"] >= 3
    assert len(r.datos["sin_ubicacion"]) >= 1
    r2 = core.orquestador.resolver(SolicitudHostAI("mover_stock_ubicacion", {"nombre":"Aceite oliva", "cantidad":4, "unidad":"l", "articulo_id":"ART-ACEITE", "origen":"Seco", "destino":"Producción"}))
    assert r2.ok, r2.mensaje
    r3 = core.orquestador.resolver(SolicitudHostAI("analizar_stock_ubicaciones", {}))
    assert any(u["ubicacion"] == "Producción" for u in r3.datos["ubicaciones"])
    print("TEST OK - Host AI 3.0.5.7 Stock por Ubicaciones")
    print("Ubicaciones:", r3.datos["total_ubicaciones"])

if __name__ == "__main__": ejecutar_prueba()
