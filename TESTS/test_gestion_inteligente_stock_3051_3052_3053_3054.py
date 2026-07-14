from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Aceite oliva", "cantidad":8, "unidad":"l", "articulo_id":"ART-ACEITE", "ubicacion":"Seco", "coste_unitario":5}))
    core.orquestador.resolver(SolicitudHostAI("ajustar_minimo_stock", {"nombre":"Aceite oliva", "cantidad_minima":10, "articulo_id":"ART-ACEITE"}))
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Harina", "cantidad":50, "unidad":"kg", "articulo_id":"ART-HARINA", "ubicacion":"", "coste_unitario":1}))
    core.orquestador.resolver(SolicitudHostAI("ajustar_minimo_stock", {"nombre":"Harina", "cantidad_minima":10, "articulo_id":"ART-HARINA"}))
    core.orquestador.resolver(SolicitudHostAI("consumir_stock", {"nombre":"Aceite oliva", "cantidad":2, "unidad":"l", "articulo_id":"ART-ACEITE", "motivo":"salida producción"}))
    a = core.orquestador.resolver(SolicitudHostAI("analizar_inteligente_stock", {"dias_sin_movimiento":0}))
    al = core.orquestador.resolver(SolicitudHostAI("generar_alertas_inteligentes_stock", {"dias_sin_movimiento":0}))
    c = core.orquestador.resolver(SolicitudHostAI("controlar_movimientos_stock", {}))
    r = core.orquestador.resolver(SolicitudHostAI("reconciliar_inteligente_stock", {"inventario_fisico":[{"nombre":"Aceite oliva","articulo_id":"ART-ACEITE","cantidad":5,"unidad":"l"},{"nombre":"Harina","articulo_id":"ART-HARINA","cantidad":50,"unidad":"kg"}]}))
    assert a.ok and al.ok and c.ok and r.ok
    assert a.datos["total_articulos"] >= 2
    assert al.datos["total_alertas"] >= 1
    assert c.datos["total_movimientos"] >= 3
    assert r.datos["total_diferencias"] >= 1
    print("TEST OK - Host AI 3.0.5.1 + 3.0.5.2 + 3.0.5.3 + 3.0.5.4 Gestión Inteligente del Stock")
    print("Analisis:", a.datos["total_articulos"])
    print("Alertas:", al.datos["total_alertas"])
    print("Movimientos:", c.datos["total_movimientos"])
    print("Diferencias:", r.datos["total_diferencias"])

if __name__ == "__main__": ejecutar_prueba()
