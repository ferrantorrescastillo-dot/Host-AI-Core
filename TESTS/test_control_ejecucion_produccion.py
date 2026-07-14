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
    plan = core.orquestador.resolver(SolicitudHostAI('planificar_inteligente_produccion', {'elaboraciones': ELABORACIONES}))
    asig = core.orquestador.resolver(SolicitudHostAI('asignar_recursos_produccion', {'elaboraciones': ELABORACIONES, 'planificacion': plan.datos}))
    avance = [
        {'clave': plan.datos['bloques'][0]['clave'], 'avance_pct': 100, 'estado': 'completada'},
        {'clave': plan.datos['bloques'][2]['clave'], 'avance_pct': 30, 'estado': 'en_curso'},
        {'clave': plan.datos['bloques'][4]['clave'], 'avance_pct': 0, 'estado': 'bloqueada'},
    ]
    r = core.orquestador.resolver(SolicitudHostAI('controlar_ejecucion_produccion', {'planificacion': plan.datos, 'asignacion': asig.datos, 'avance': avance, 'minuto_actual': 200}))
    assert r.ok, r.mensaje
    assert r.datos['version'] == '3.0.6.5'
    assert r.datos['total_tareas'] >= 3
    assert r.datos['bloqueadas'] >= 1
    assert r.datos['riesgo_global'] in {'ok','aviso','critico'}
    print('TEST OK - Host AI 3.0.6.5 Control Inteligente de Ejecución de Producción')

if __name__ == '__main__': ejecutar_prueba()
