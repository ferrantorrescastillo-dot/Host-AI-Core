from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI


def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    limpiar = core.orquestador.resolver(SolicitudHostAI('limpiar_memoria_conversacional_308', {}))
    assert limpiar.ok, limpiar.mensaje
    r = core.orquestador.resolver(SolicitudHostAI('recordar_memoria_conversacional_308', {
        'clave': 'ultimo_articulo', 'valor': 'aceite de oliva', 'tipo': 'articulo', 'prioridad': 5, 'tags': ['stock','compras']
    }))
    assert r.ok, r.mensaje
    c = core.orquestador.resolver(SolicitudHostAI('consultar_memoria_conversacional_308', {'clave': 'ultimo_articulo'}))
    assert c.ok, c.mensaje
    assert c.datos['total_entradas'] >= 1
    ref = core.orquestador.resolver(SolicitudHostAI('resolver_referencias_memoria_308', {'texto': 'haz lo mismo con ese producto'}))
    assert ref.ok, ref.mensaje
    assert 'ultimo_articulo' in ref.datos['referencias_resueltas']
    print('TEST OK - Host AI 3.0.8.5 Memoria Conversacional')
    print('Entradas:', c.datos['total_entradas'])
    print('Referencias:', len(ref.datos['referencias_resueltas']))

if __name__ == '__main__': ejecutar_prueba()
