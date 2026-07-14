from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI
ESCANDALLOS = [
    {'nombre':'Paella marisco','raciones':10,'precio_venta_por_racion':18,'tiempo_activo_min':90,'tiempo_pasivo_min':30,'ingredientes':[{'nombre':'Arroz','cantidad':1,'unidad':'kg','precio_unitario':2.4,'proveedor':'Proveedor A'},{'nombre':'Caldo','cantidad':3,'unidad':'l','precio_unitario':1.2,'proveedor':'Proveedor A'},{'nombre':'Gamba','cantidad':1.2,'unidad':'kg','precio_unitario':14,'merma_pct':8,'proveedor':'Proveedor B'}]},
    {'nombre':'Receta problemática','raciones':8,'precio_venta_por_racion':5,'tiempo_activo_min':180,'tiempo_pasivo_min':120,'ingredientes':[{'nombre':'Aceite','cantidad':1,'unidad':'l','precio_unitario':0},{'nombre':'Carne','cantidad':4,'unidad':'kg','precio_unitario':12,'merma_pct':40,'proveedor':'Proveedor C'}]},
]
HISTORICO = [
    {'nombre':'Paella marisco','coste_total':18.0,'precio_venta':170},
    {'nombre':'Paella marisco','coste_total':20.0,'precio_venta':175},
    {'nombre':'Paella marisco','coste_total':22.8,'precio_venta':180},
    {'nombre':'Receta problemática','coste_total':42.0,'precio_venta':40},
    {'nombre':'Receta problemática','coste_total':45.0,'precio_venta':40},
    {'nombre':'Receta problemática','coste_total':49.0,'precio_venta':40},
]
VENTAS = [
    {'nombre':'Paella marisco','unidades_vendidas':120},
    {'nombre':'Receta problemática','unidades_vendidas':12},
]


def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    a = core.orquestador.resolver(SolicitudHostAI('analizar_inteligente_escandallos', {'escandallos': ESCANDALLOS})); assert a.ok, a.mensaje
    p = core.orquestador.resolver(SolicitudHostAI('predecir_inteligente_rentabilidad', {'analisis': a.datos, 'historico': HISTORICO})); assert p.ok, p.mensaje
    o = core.orquestador.resolver(SolicitudHostAI('optimizar_carta_inteligente', {'analisis': a.datos, 'prediccion': p.datos, 'ventas': VENTAS})); assert o.ok, o.mensaje
    assert o.datos['version'] == '3.0.7.7'
    assert o.datos['total_platos'] == 2
    assert o.datos['resumen']['total_platos'] == 2
    print('TEST OK - Host AI 3.0.7.7 Motor Inteligente de Optimización de Carta')
    print('Platos:', o.datos['total_platos'])
    print('Estrella:', o.datos['platos_estrella'])
    print('Revisar/retirar:', o.datos['platos_a_revisar'] + o.datos['platos_a_retirar'])

if __name__ == '__main__': ejecutar_prueba()
