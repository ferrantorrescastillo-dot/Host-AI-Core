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
    asign = core.orquestador.resolver(SolicitudHostAI('asignar_recursos_produccion', {'elaboraciones': ELABORACIONES, 'planificacion': plan.datos}))
    control = core.orquestador.resolver(SolicitudHostAI('controlar_ejecucion_produccion', {'planificacion': plan.datos, 'asignacion': asign.datos, 'avance': [], 'minuto_actual': 260}))
    replan = core.orquestador.resolver(SolicitudHostAI('replanificar_inteligente_produccion', {'control': control.datos}))
    r = core.orquestador.resolver(SolicitudHostAI('optimizar_inteligente_produccion', {'planificacion': plan.datos, 'asignacion': asign.datos, 'control': control.datos, 'replanificacion': replan.datos}))
    assert r.ok, r.mensaje
    assert r.datos['version'] == '3.0.6.7'
    assert 'oportunidades' in r.datos
    assert 'plan_optimizado' in r.datos
    assert r.datos['total_oportunidades'] >= 1
    print('TEST OK - Host AI 3.0.6.7 Optimizador Inteligente de Producción')
    print('Oportunidades:', r.datos['total_oportunidades'])
    print('Ahorro estimado:', r.datos['ahorro_total_min_estimado'])

if __name__ == '__main__': ejecutar_prueba()
