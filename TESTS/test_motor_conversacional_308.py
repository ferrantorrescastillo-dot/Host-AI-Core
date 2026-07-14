from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    l = core.orquestador.resolver(SolicitudHostAI('limpiar_conversacion_308', {})); assert l.ok, l.mensaje
    r1 = core.orquestador.resolver(SolicitudHostAI('conversar_host_ai_308', {'texto': '¿Cuánto aceite tengo en stock hoy?'})); assert r1.ok, r1.mensaje
    r2 = core.orquestador.resolver(SolicitudHostAI('conversar_host_ai_308', {'texto': '¿Y mañana qué debería comprar?'})); assert r2.ok, r2.mensaje
    h = core.orquestador.resolver(SolicitudHostAI('historial_conversacional_308', {})); assert h.ok, h.mensaje
    assert r1.datos['version'] == '3.0.8.2'
    assert h.datos['total_turnos'] == 2
    assert r2.datos['contexto_actualizado']['ultima_intencion']
    print('TEST OK - Host AI 3.0.8.2 Motor Conversacional')
    print('Turnos:', h.datos['total_turnos'])
    print('Última intención:', r2.datos['contexto_actualizado']['ultima_intencion'])

if __name__ == '__main__': ejecutar_prueba()
