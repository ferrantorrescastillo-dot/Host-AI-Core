from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    for prov, precios in {"PROV-A":[10,10.1,10.2,10.1], "PROV-B":[9,14,8,15]}.items():
        for precio in precios:
            core.orquestador.resolver(SolicitudHostAI("registrar_precio_historico", {"registro": {"articulo_id":"ART-ACEITE", "nombre_articulo":"Aceite", "precio": precio, "unidad":"l", "proveedor_id": prov, "proveedor_nombre": prov}}))
    r = core.orquestador.resolver(SolicitudHostAI("comparar_inteligente_proveedores_compras", {}))
    assert r.ok is True
    assert r.datos["total_proveedores"] >= 2
    assert r.datos["mejor_proveedor"]
    a = core.orquestador.resolver(SolicitudHostAI("comparar_inteligente_proveedores_articulo", {"articulo_id":"ART-ACEITE"}))
    assert a.ok is True
    assert len(a.datos["comparaciones"]) >= 2
    print("TEST OK - Host AI 3.0.4.5 Comparador Inteligente de Proveedores")
    print("Proveedores:", r.datos["total_proveedores"])

if __name__ == "__main__": ejecutar_prueba()
