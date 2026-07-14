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
    r = core.orquestador.resolver(SolicitudHostAI('generar_alertas_produccion', {'elaboraciones': ELABORACIONES, 'jornada_horas':7.5, 'cocineros':2}))
    assert r.ok, r.mensaje
    assert r.datos['version'] == '3.0.6.2'
    assert r.datos['total_alertas'] >= 1
    assert any(a['tipo'] in ('elaboracion_riesgo_alto','dependencias','pasivo_largo') for a in r.datos['alertas'])
    print('TEST OK - Host AI 3.0.6.2 Motor de Alertas de Producción')
    print('Alertas:', r.datos['total_alertas'])

if __name__ == '__main__': ejecutar_prueba()
