from pathlib import Path
import sys
from datetime import date, timedelta
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Aceite", "cantidad":2, "unidad":"l", "articulo_id":"ART-ACEITE", "ubicacion":"Seco", "coste_unitario":5.0}))
    core.orquestador.resolver(SolicitudHostAI("ajustar_minimo_stock", {"nombre":"Aceite", "cantidad_minima":5, "articulo_id":"ART-ACEITE"}))
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Yogur", "cantidad":4, "unidad":"u", "articulo_id":"ART-YOGUR", "ubicacion":"Cámara", "caducidad":(date.today()+timedelta(days=1)).isoformat(), "coste_unitario":0.6}))
    analisis = core.orquestador.resolver(SolicitudHostAI("analizar_inteligente_stock", {"dias_sin_movimiento":0}))
    alertas = core.orquestador.resolver(SolicitudHostAI("generar_alertas_inteligentes_stock", {"dias_caducidad_alerta":3, "dias_sin_movimiento":0}))
    assert analisis.ok is True
    assert alertas.ok is True
    assert analisis.datos["total_articulos"] >= 2
    assert alertas.datos["total_alertas"] >= 2
    print("TEST OK - Host AI 3.0.5.1 + 3.0.5.2 Gestión Inteligente del Stock")
    print("Analisis stock:", analisis.datos["total_articulos"])
    print("Alertas stock:", alertas.datos["total_alertas"])

if __name__ == "__main__": ejecutar_prueba()
