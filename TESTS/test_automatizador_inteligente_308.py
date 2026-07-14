from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI


def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    prep = core.orquestador.resolver(SolicitudHostAI('preparar_automatizacion_308', {'texto': 'crea un pedido de aceite para mañana'}))
    assert prep.ok, prep.mensaje
    assert prep.datos['version'] == '3.0.8.6'
    assert prep.datos['accion_detectada'] == 'crear_pedido'
    assert prep.datos['requiere_confirmacion'] is True
    val = core.orquestador.resolver(SolicitudHostAI('validar_confirmacion_automatizacion_308', {'plan': prep.datos, 'confirmado': False}))
    assert val.ok, val.mensaje
    assert val.datos['puede_ejecutarse'] is False
    ejec = core.orquestador.resolver(SolicitudHostAI('ejecutar_automatizacion_308', {'texto': 'crea un pedido de aceite para mañana', 'confirmado': False}))
    assert ejec.ok, ejec.mensaje
    assert ejec.datos['ejecutada'] is False
    print('TEST OK - Host AI 3.0.8.6 Automatizador Inteligente')
    print('Acción:', prep.datos['accion_detectada'])
    print('Riesgos:', len(prep.datos['riesgos']))

if __name__ == '__main__': ejecutar_prueba()
