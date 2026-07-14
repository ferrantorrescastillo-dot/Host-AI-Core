from pathlib import Path
import sys
BASE_DIR=Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0,str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI
def ejecutar_prueba():
    core=HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    core.orquestador.resolver(SolicitudHostAI("registrar_movimiento_stock_historico",{"movimiento":{"articulo_id":"ART-CARRILLERA","nombre_articulo":"Carrillera de ternera","tipo":"entrada","cantidad":8,"unidad":"kg","proveedor_id":"PROV-MAKRO"}}))
    r=core.orquestador.resolver(SolicitudHostAI("generar_recomendaciones_compras",{}))
    assert r.ok and r.datos["total"]>=1
    e=core.orquestador.resolver(SolicitudHostAI("exportar_recomendaciones_compras",{"recomendaciones":r.datos,"nombre":"test_recomendaciones_compras.json"}))
    assert e.ok and Path(e.datos["archivo"]).exists()
    print("TEST OK - Host AI 3.0.4.2 Motor Recomendaciones Compras")
if __name__=="__main__": ejecutar_prueba()
