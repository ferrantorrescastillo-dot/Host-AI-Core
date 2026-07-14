from pathlib import Path
import sys
BASE_DIR=Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0,str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI
ESCANDALLOS=[
 {'nombre':'Paella marisco','raciones':10,'precio_venta_por_racion':18,'tiempo_activo_min':90,'ingredientes':[{'nombre':'Arroz','cantidad':1,'unidad':'kg','precio_unitario':2.4,'proveedor':'Proveedor A'},{'nombre':'Caldo','cantidad':3,'unidad':'l','precio_unitario':1.2,'proveedor':'Proveedor A'},{'nombre':'Gamba','cantidad':1.2,'unidad':'kg','precio_unitario':14,'merma_pct':8,'proveedor':'Proveedor B'}]},
 {'nombre':'Receta problemática','raciones':8,'precio_venta_por_racion':5,'ingredientes':[{'nombre':'Aceite','cantidad':1,'unidad':'l','precio_unitario':0},{'nombre':'Carne','cantidad':4,'unidad':'kg','precio_unitario':12,'merma_pct':40,'proveedor':'Proveedor C'}]},
]
ESCANDALLOS_ANT=[
 {'nombre':'Paella marisco','raciones':10,'precio_venta_por_racion':18,'tiempo_activo_min':90,'ingredientes':[{'nombre':'Arroz','cantidad':1,'unidad':'kg','precio_unitario':2.1,'proveedor':'Proveedor A'},{'nombre':'Caldo','cantidad':3,'unidad':'l','precio_unitario':1.0,'proveedor':'Proveedor A'},{'nombre':'Gamba','cantidad':1.2,'unidad':'kg','precio_unitario':11,'merma_pct':8,'proveedor':'Proveedor B'}]},
 {'nombre':'Receta antigua','raciones':5,'precio_venta_por_racion':8,'ingredientes':[{'nombre':'Patata','cantidad':2,'unidad':'kg','precio_unitario':1.2}]},
]

def ejecutar_prueba():
    core=HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    c=core.orquestador.resolver(SolicitudHostAI('comparar_historico_escandallos',{'escandallos_anteriores':ESCANDALLOS_ANT,'escandallos_actuales':ESCANDALLOS}))
    assert c.ok, c.mensaje
    assert c.datos['version']=='3.0.7.4'
    assert c.datos['total_comparaciones']>=2
    assert c.datos['resumen']['subidas_coste']>=1
    print('TEST OK - Host AI 3.0.7.4 Comparador Histórico de Escandallos')
    print('Comparaciones:', c.datos['total_comparaciones'])
if __name__=='__main__': ejecutar_prueba()
