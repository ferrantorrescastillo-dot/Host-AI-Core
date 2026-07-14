from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    analisis = core.orquestador.resolver(SolicitudHostAI('analizar_lenguaje_natural', {'texto': '¿Qué proveedor me conviene para comprar aceite mañana?'}))
    assert analisis.ok, analisis.mensaje
    sel = core.orquestador.resolver(SolicitudHostAI('seleccionar_motor_host_ai_308', {'texto': '¿Qué proveedor me conviene para comprar aceite mañana?', 'analisis': analisis.datos}))
    assert sel.ok, sel.mensaje
    assert sel.datos['version'] == '3.0.8.3'
    assert sel.datos['pipeline_seleccionado']
    assert 'solicitud_host_ai' in sel.datos
    print('TEST OK - Host AI 3.0.8.3 Selector Inteligente de Motores')
    print('Motor:', sel.datos['pipeline_seleccionado'])
    print('Acción:', sel.datos['accion_seleccionada'])

if __name__ == '__main__': ejecutar_prueba()
