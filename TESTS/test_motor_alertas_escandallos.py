from pathlib import Path
import sys
BASE_DIR=Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0,str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

ESCANDALLOS=[
 {'nombre':'Receta sin precio ingrediente','raciones':10,'precio_venta_por_racion':8,'ingredientes':[{'nombre':'Aceite','cantidad':1,'unidad':'l','precio_unitario':0},{'nombre':'Aceite','cantidad':0.2,'unidad':'l','precio_unitario':0},{'nombre':'Merluza','cantidad':2,'unidad':'kg','precio_unitario':14,'merma_pct':45}]},
 {'nombre':'Receta sin venta','raciones':5,'precio_venta_por_racion':0,'ingredientes':[{'nombre':'Arroz','cantidad':1,'unidad':'kg','precio_unitario':2}]},
]

def ejecutar_prueba():
    core=HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    r=core.orquestador.resolver(SolicitudHostAI('generar_alertas_escandallos',{'escandallos':ESCANDALLOS}))
    assert r.ok, r.mensaje
    assert r.datos['version']=='3.0.7.2'
    assert r.datos['total_alertas']>=4
    tipos={a['tipo'] for a in r.datos['alertas']}
    assert 'ingrediente_sin_precio' in tipos
    assert 'merma_excesiva' in tipos
    assert 'sin_precio_venta' in tipos
    print('TEST OK - Host AI 3.0.7.2 Motor de Alertas de Escandallos')
    print('Alertas:', r.datos['total_alertas'])
if __name__=='__main__': ejecutar_prueba()
