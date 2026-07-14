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
    r3 = core.orquestador.resolver(SolicitudHostAI('planificar_inteligente_produccion', {'elaboraciones': ELABORACIONES}))
    r4 = core.orquestador.resolver(SolicitudHostAI('asignar_recursos_produccion', {'elaboraciones': ELABORACIONES, 'planificacion': r3.datos}))
    avance = [
        {'clave': r3.datos['bloques'][0]['clave'], 'avance_pct': 100, 'estado': 'completada'},
        {'clave': r3.datos['bloques'][2]['clave'], 'avance_pct': 20, 'estado': 'en_curso'},
        {'clave': r3.datos['bloques'][4]['clave'], 'avance_pct': 0, 'estado': 'bloqueada'},
    ]
    r5 = core.orquestador.resolver(SolicitudHostAI('controlar_ejecucion_produccion', {'planificacion': r3.datos, 'asignacion': r4.datos, 'avance': avance, 'minuto_actual': 220}))
    r6 = core.orquestador.resolver(SolicitudHostAI('replanificar_inteligente_produccion', {'control': r5.datos, 'cocineros_disponibles': 3}))
    for r in (r1,r2,r3,r4,r5,r6): assert r.ok, r.mensaje
    assert r1.datos['version'] == '3.0.6.1'
    assert r2.datos['version'] == '3.0.6.2'
    assert r3.datos['version'] == '3.0.6.3'
    assert r4.datos['version'] == '3.0.6.4'
    assert r5.datos['version'] == '3.0.6.5'
    assert r6.datos['version'] == '3.0.6.6'
    print('TEST OK - Host AI 3.0.6.1 + 3.0.6.2 + 3.0.6.3 + 3.0.6.4 + 3.0.6.5 + 3.0.6.6 Producción')
    print('Analisis:', r1.datos['total_elaboraciones'])
    print('Alertas:', r2.datos['total_alertas'])
    print('Bloques:', r3.datos['total_bloques'])
    print('Asignaciones:', r4.datos['total_asignaciones'])
    print('Control tareas:', r5.datos['total_tareas'])
    print('Replanificaciones:', r6.datos['total_acciones'])

if __name__ == '__main__': ejecutar_prueba()
