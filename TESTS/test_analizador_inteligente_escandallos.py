from pathlib import Path
import sys
BASE_DIR=Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0,str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

ESCANDALLOS=[
 {'nombre':'Paella marisco','raciones':10,'precio_venta_por_racion':18,'tiempo_activo_min':90,'ingredientes':[{'nombre':'Arroz','cantidad':1,'unidad':'kg','precio_unitario':2.4},{'nombre':'Caldo','cantidad':3,'unidad':'l','precio_unitario':1.2},{'nombre':'Gamba','cantidad':1.2,'unidad':'kg','precio_unitario':14,'merma_pct':8}]},
 {'nombre':'Croqueta chuletón','raciones':40,'precio_venta_por_racion':2.2,'tiempo_activo_min':120,'ingredientes':[{'nombre':'Leche','cantidad':3,'unidad':'l','precio_unitario':1.1},{'nombre':'Chuletón','cantidad':1.5,'unidad':'kg','precio_unitario':18,'merma_pct':10},{'nombre':'Harina','cantidad':0.5,'unidad':'kg','precio_unitario':0.9}]},
]

def ejecutar_prueba():
    core=HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    r=core.orquestador.resolver(SolicitudHostAI('analizar_inteligente_escandallos',{'escandallos':ESCANDALLOS,'coste_hora_cocinero':18,'pct_costes_ocultos':4}))
    assert r.ok, r.mensaje
    assert r.datos['version']=='3.0.7.1'
    assert r.datos['total_escandallos']==2
    assert r.datos['coste_total']>0
    assert r.datos['venta_total']>0
    assert r.datos['food_cost_medio_pct']>=0
    print('TEST OK - Host AI 3.0.7.1 Analizador Inteligente de Escandallos')
    print('Escandallos:', r.datos['total_escandallos'])
    print('Food cost medio:', r.datos['food_cost_medio_pct'])
if __name__=='__main__': ejecutar_prueba()
