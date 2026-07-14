from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    seleccion = core.orquestador.resolver(SolicitudHostAI('seleccionar_motor_host_ai_308', {'texto': 'Analiza el stock de aceite'}))
    assert seleccion.ok, seleccion.mensaje
    resultado = {'ok': True, 'mensaje': 'Stock analizado correctamente.', 'datos': {'articulos': [{'nombre':'aceite'}], 'alertas': [], 'lectura_host_ai': 'El stock de aceite queda revisado.'}}
    resp = core.orquestador.resolver(SolicitudHostAI('generar_respuesta_host_ai_308', {'resultado': resultado, 'seleccion': seleccion.datos}))
    assert resp.ok, resp.mensaje
    assert resp.datos['version'] == '3.0.8.4'
    assert resp.datos['resumen']
    assert isinstance(resp.datos['detalle'], list)
    print('TEST OK - Host AI 3.0.8.4 Generador Inteligente de Respuestas')
    print('Título:', resp.datos['titulo'])
    print('Detalle:', len(resp.datos['detalle']))

if __name__ == '__main__': ejecutar_prueba()
