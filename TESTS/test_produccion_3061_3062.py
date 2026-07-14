from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

ELABORACIONES = [
    {'nombre':'Fondo oscuro','cantidad':20,'unidad':'l','tiempo_activo_min':45,'tiempo_pasivo_min':240,'recursos':['horno','olla'],'prioridad':'critica'},
    {'nombre':'Carrilleras braseadas','cantidad':12,'unidad':'kg','tiempo_activo_min':110,'tiempo_pasivo_min':180,'recursos':['horno','fogón'],'prioridad':'alta','dependencias':['Fondo oscuro']},
    {'nombre':'Romesco','cantidad':5,'unidad':'kg','tiempo_activo_min':55,'tiempo_pasivo_min':20,'recursos':['horno','robot'],'prioridad':'normal'},
]


def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    r1 = core.orquestador.resolver(SolicitudHostAI('analizar_inteligente_produccion', {'elaboraciones': ELABORACIONES}))
    r2 = core.orquestador.resolver(SolicitudHostAI('generar_alertas_produccion', {'elaboraciones': ELABORACIONES}))
    assert r1.ok, r1.mensaje
    assert r2.ok, r2.mensaje
    assert r1.datos['version'] == '3.0.6.1'
    assert r2.datos['version'] == '3.0.6.2'
    print('TEST OK - Host AI 3.0.6.1 + 3.0.6.2 Producción')
    print('Analisis:', r1.datos['total_elaboraciones'])
    print('Alertas:', r2.datos['total_alertas'])

if __name__ == '__main__': ejecutar_prueba()
