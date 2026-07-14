from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def cargar_datos(core):
    for prov, precios in {"PROV-A":[10,10.2,10.4,20,21], "PROV-B":[9.8,9.9,10.0,10.1]}.items():
        for precio in precios:
            core.orquestador.resolver(SolicitudHostAI("registrar_precio_historico", {"registro": {"articulo_id":"ART-ACEITE", "nombre_articulo":"Aceite", "precio":precio, "unidad":"l", "proveedor_id":prov, "proveedor_nombre":prov}}))
    for tipo,cantidad in [("entrada",20),("salida",5),("salida",4),("salida",6),("salida",5)]:
        core.orquestador.resolver(SolicitudHostAI("registrar_movimiento_stock_historico", {"movimiento": {"articulo_id":"ART-ACEITE", "nombre_articulo":"Aceite", "tipo":tipo, "cantidad":cantidad, "unidad":"l", "proveedor_id":"PROV-A"}}))

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria(); cargar_datos(core)
    r = core.orquestador.resolver(SolicitudHostAI("generar_pedidos_inteligentes", {"horizonte_dias": 14, "dias_seguridad": 3}))
    assert r.ok is True
    assert r.datos["total_decisiones"] >= 1
    assert any(d["articulo_id"] == "ART-ACEITE" for d in r.datos["decisiones"])
    a = core.orquestador.resolver(SolicitudHostAI("generar_pedido_inteligente_articulo", {"articulo_id":"ART-ACEITE"}))
    assert a.ok is True
    print("TEST OK - Host AI 3.0.4.7 Motor Inteligente de Pedidos")
    print("Decisiones:", r.datos["total_decisiones"])
    print("Comprar:", r.datos["comprar"])
    print("Esperar:", r.datos["esperar"])

if __name__ == "__main__": ejecutar_prueba()
