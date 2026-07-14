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
    core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {"nombre":"Harina", "cantidad":40, "unidad":"kg", "articulo_id":"ART-HARINA", "ubicacion":"", "coste_unitario":1}))
    pruebas = [
        ("analizar_inteligente_stock", {}),
        ("generar_alertas_inteligentes_stock", {}),
        ("controlar_movimientos_stock", {}),
        ("reconciliar_inteligente_stock", {}),
        ("predecir_necesidades_stock", {"horizonte_dias":14}),
        ("optimizar_stock", {"horizonte_dias":14}),
        ("analizar_stock_ubicaciones", {}),
        ("cerrar_gestion_inteligente_stock", {"horizonte_dias":14}),
    ]
    resultados=[]
    for intencion, parametros in pruebas:
        r = core.orquestador.resolver(SolicitudHostAI(intencion, parametros))
        assert r.ok, f"{intencion}: {r.mensaje}"
        resultados.append(r)
    assert resultados[-1].datos["version"] == "3.0.5"
    print("TEST OK - Host AI 3.0.5.1 + 3.0.5.2 + 3.0.5.3 + 3.0.5.4 + 3.0.5.5 + 3.0.5.6 + 3.0.5.7 + 3.0.5.8 Gestión Inteligente del Stock")
    print("Artículos:", resultados[0].datos["total_articulos"])
    print("Alertas:", resultados[1].datos.get("total_alertas", resultados[1].datos.get("total_avisos", 0)))
    print("Ubicaciones:", resultados[6].datos["total_ubicaciones"])
    print("Estado cierre:", resultados[7].datos["estado_general"])

if __name__ == "__main__": ejecutar_prueba()
