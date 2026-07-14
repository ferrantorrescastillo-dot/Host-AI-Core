from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    r = core.orquestador.resolver(SolicitudHostAI('asistente_host_ai_308', {'texto': 'qué debo comprar mañana', 'ejecutar': False}))
    assert r.ok, r.mensaje
    assert r.datos.get('version') == '3.0.8.7'
    assert r.datos.get('pipeline_usado')
    assert r.datos.get('respuesta_final')
    diag = core.orquestador.resolver(SolicitudHostAI('diagnosticar_asistente_host_ai_308', {}))
    assert diag.ok, diag.mensaje
    print('TEST OK - Host AI 3.0.8.7 Asistente Inteligente Host AI')
    print('Pipeline usado:', r.datos.get('pipeline_usado'))
    print('Requiere confirmación:', r.datos.get('requiere_confirmacion'))

if __name__ == '__main__': ejecutar_prueba()
