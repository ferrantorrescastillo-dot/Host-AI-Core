from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    a = core.orquestador.resolver(SolicitudHostAI('analizar_lenguaje_natural', {'texto': 'Organízame la producción de mañana para la paella'})); assert a.ok, a.mensaje
    c = core.orquestador.resolver(SolicitudHostAI('conversar_host_ai_308', {'texto': 'Organízame la producción de mañana para la paella'})); assert c.ok, c.mensaje
    h = core.orquestador.resolver(SolicitudHostAI('historial_conversacional_308', {})); assert h.ok, h.mensaje
    assert a.datos['version'] == '3.0.8.1'
    assert c.datos['version'] == '3.0.8.2'
    assert h.datos['total_turnos'] >= 1
    print('TEST OK - Host AI 3.0.8.1 + 3.0.8.2 IA Conversacional')
    print('Intención:', a.datos['intencion_detectada'])
    print('Pipeline:', a.datos['pipeline_sugerido'])
    print('Turnos:', h.datos['total_turnos'])

if __name__ == '__main__': ejecutar_prueba()
