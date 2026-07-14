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
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Tomate", "cantidad":12, "unidad":"kg", "articulo_id":"ART-TOMATE", "ubicacion":"Cámara", "coste_unitario":2}))
    core.orquestador.resolver(SolicitudHostAI("registrar_salida_stock", {"nombre":"Tomate", "cantidad":2, "unidad":"kg", "articulo_id":"ART-TOMATE", "motivo":"producción"}))
    r = core.orquestador.resolver(SolicitudHostAI("cerrar_gestion_inteligente_stock", {"horizonte_dias":14}))
    assert r.ok, r.mensaje
    assert r.datos["version"] == "3.0.5"
    assert len(r.datos["modulos_validados"]) >= 7
    assert "total_articulos" in r.datos["metricas"]
    print("TEST OK - Host AI 3.0.5.8 Cierre Gestión Inteligente del Stock")
    print("Estado:", r.datos["estado_general"])

if __name__ == "__main__": ejecutar_prueba()
