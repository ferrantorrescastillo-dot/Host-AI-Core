from pathlib import Path
import sys
BASE_DIR=Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0,str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

ESCANDALLOS=[
 {'nombre':'Paella marisco','raciones':10,'precio_venta_por_racion':18,'tiempo_activo_min':90,'ingredientes':[{'nombre':'Arroz','cantidad':1,'unidad':'kg','precio_unitario':2.4},{'nombre':'Caldo','cantidad':3,'unidad':'l','precio_unitario':1.2},{'nombre':'Gamba','cantidad':1.2,'unidad':'kg','precio_unitario':14,'merma_pct':8}]},
 {'nombre':'Receta problemática','raciones':8,'precio_venta_por_racion':5,'ingredientes':[{'nombre':'Aceite','cantidad':1,'unidad':'l','precio_unitario':0},{'nombre':'Carne','cantidad':4,'unidad':'kg','precio_unitario':12,'merma_pct':40}]},
]

def ejecutar_prueba():
    core=HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    a=core.orquestador.resolver(SolicitudHostAI('analizar_inteligente_escandallos',{'escandallos':ESCANDALLOS}))
    assert a.ok, a.mensaje
    b=core.orquestador.resolver(SolicitudHostAI('generar_alertas_escandallos',{'analisis':a.datos}))
    assert b.ok, b.mensaje
    assert a.datos['version']=='3.0.7.1'
    assert b.datos['version']=='3.0.7.2'
    assert a.datos['total_escandallos']==2
    assert b.datos['total_alertas']>=2
    print('TEST OK - Host AI 3.0.7.1 + 3.0.7.2 Escandallos Inteligentes')
    print('Escandallos:', a.datos['total_escandallos'])
    print('Alertas:', b.datos['total_alertas'])
if __name__=='__main__': ejecutar_prueba()
