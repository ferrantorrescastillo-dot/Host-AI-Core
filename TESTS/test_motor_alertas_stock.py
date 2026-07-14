from pathlib import Path
import sys
from datetime import date, timedelta
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Leche", "cantidad":1, "unidad":"l", "articulo_id":"ART-LECHE", "ubicacion":"Cámara", "caducidad":(date.today()+timedelta(days=1)).isoformat(), "coste_unitario":1.2}))
    core.orquestador.resolver(SolicitudHostAI("ajustar_minimo_stock", {"nombre":"Leche", "cantidad_minima":8, "articulo_id":"ART-LECHE"}))
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Producto sin ubicación", "cantidad":3, "unidad":"kg", "articulo_id":"ART-SINUBI", "ubicacion":"", "coste_unitario":2.0}))
    r = core.orquestador.resolver(SolicitudHostAI("generar_alertas_inteligentes_stock", {"dias_caducidad_alerta":3, "dias_sin_movimiento":0}))
    assert r.ok is True
    assert r.datos["total_alertas"] >= 3
    assert r.datos["criticas"] >= 1
    tipos = {a["tipo"] for a in r.datos["alertas"]}
    assert "stock_bajo" in tipos
    assert "caducidad_cercana" in tipos
    assert "sin_ubicacion" in tipos
    print("TEST OK - Host AI 3.0.5.2 Motor de Alertas de Stock")
    print("Alertas:", r.datos["total_alertas"])

if __name__ == "__main__": ejecutar_prueba()
