from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI


def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Aceite oliva", "cantidad":5, "unidad":"l", "articulo_id":"ART-ACEITE", "ubicacion":"Seco", "coste_unitario":5}))
    core.orquestador.resolver(SolicitudHostAI("ajustar_minimo_stock", {"nombre":"Aceite oliva", "cantidad_minima":10, "articulo_id":"ART-ACEITE"}))
    core.orquestador.resolver(SolicitudHostAI("consumir_stock", {"nombre":"Aceite oliva", "cantidad":2, "unidad":"l", "articulo_id":"ART-ACEITE", "motivo":"producción"}))
    produccion=[{"ingredientes":[{"nombre":"Aceite oliva","articulo_id":"ART-ACEITE","cantidad":6,"unidad":"l"}]}]
    r = core.orquestador.resolver(SolicitudHostAI("predecir_necesidades_stock", {"horizonte_dias":7, "produccion_prevista": produccion}))
    assert r.ok, r.mensaje
    assert r.datos["total_necesidades"] >= 1
    assert r.datos["items"][0]["cantidad_a_reponer"] > 0
    assert r.datos["items"][0]["confianza"] > 0
    print("TEST OK - Host AI 3.0.5.5 Predicción de Necesidades de Stock")
    print("Necesidades:", r.datos["total_necesidades"])

if __name__ == "__main__": ejecutar_prueba()
