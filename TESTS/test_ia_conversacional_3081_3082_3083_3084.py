from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    texto = 'Organízame la producción de mañana y dime qué motor debe usar Host AI'
    a = core.orquestador.resolver(SolicitudHostAI('analizar_lenguaje_natural', {'texto': texto})); assert a.ok, a.mensaje
    c = core.orquestador.resolver(SolicitudHostAI('conversar_host_ai_308', {'texto': texto})); assert c.ok, c.mensaje
    s = core.orquestador.resolver(SolicitudHostAI('seleccionar_motor_host_ai_308', {'texto': texto, 'analisis': a.datos})); assert s.ok, s.mensaje
    g = core.orquestador.resolver(SolicitudHostAI('generar_respuesta_host_ai_308', {'resultado': {'ok': True, 'mensaje': s.datos['lectura_host_ai'], 'datos': {'seleccion': s.datos, 'analisis': a.datos}}, 'seleccion': s.datos})); assert g.ok, g.mensaje
    assert a.datos['version'] == '3.0.8.1'
    assert c.datos['version'] == '3.0.8.2'
    assert s.datos['version'] == '3.0.8.3'
    assert g.datos['version'] == '3.0.8.4'
    print('TEST OK - Host AI 3.0.8.1 + 3.0.8.2 + 3.0.8.3 + 3.0.8.4 IA Conversacional')
    print('Intención:', a.datos['intencion_detectada'])
    print('Motor:', s.datos['pipeline_seleccionado'])
    print('Respuesta:', g.datos['titulo'])

if __name__ == '__main__': ejecutar_prueba()
