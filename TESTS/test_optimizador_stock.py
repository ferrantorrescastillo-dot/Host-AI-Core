from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI


def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Aceite oliva", "cantidad":3, "unidad":"l", "articulo_id":"ART-ACEITE", "ubicacion":"Seco", "coste_unitario":5}))
    core.orquestador.resolver(SolicitudHostAI("ajustar_minimo_stock", {"nombre":"Aceite oliva", "cantidad_minima":10, "articulo_id":"ART-ACEITE"}))
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Harina", "cantidad":80, "unidad":"kg", "articulo_id":"ART-HARINA", "ubicacion":"", "coste_unitario":1}))
    core.orquestador.resolver(SolicitudHostAI("ajustar_minimo_stock", {"nombre":"Harina", "cantidad_minima":10, "articulo_id":"ART-HARINA"}))
    r = core.orquestador.resolver(SolicitudHostAI("optimizar_stock", {"horizonte_dias":14}))
    assert r.ok, r.mensaje
    assert r.datos["total_recomendaciones"] >= 2
    assert any(a["accion"] == "comprar" for a in r.datos["acciones"])
    assert any(a["accion"] in {"no_comprar_y_consumir_antes", "asignar_ubicacion", "revisar_uso_o_baja"} for a in r.datos["acciones"])
    print("TEST OK - Host AI 3.0.5.6 Optimizador de Stock")
    print("Recomendaciones:", r.datos["total_recomendaciones"])

if __name__ == "__main__": ejecutar_prueba()
