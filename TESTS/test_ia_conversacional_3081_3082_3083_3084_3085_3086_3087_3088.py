from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    core.orquestador.resolver(SolicitudHostAI('limpiar_memoria_conversacional_308', {}))
    a = core.orquestador.resolver(SolicitudHostAI('analizar_lenguaje_natural', {'texto': 'cuánto stock tengo de aceite'}))
    assert a.ok, a.mensaje
    conv = core.orquestador.resolver(SolicitudHostAI('conversar_host_ai_308', {'texto': 'cuánto stock tengo de aceite'}))
    assert conv.ok, conv.mensaje
    sel = core.orquestador.resolver(SolicitudHostAI('seleccionar_motor_host_ai_308', {'texto': 'cuánto stock tengo de aceite', 'analisis': a.datos}))
    assert sel.ok, sel.mensaje
    resp = core.orquestador.resolver(SolicitudHostAI('generar_respuesta_host_ai_308', {'resultado': {'ok': True, 'mensaje': 'Consulta procesada', 'datos': {'articulos': ['aceite']}}, 'seleccion': sel.datos}))
    assert resp.ok, resp.mensaje
    mem = core.orquestador.resolver(SolicitudHostAI('recordar_memoria_conversacional_308', {'clave': 'ultimo_articulo', 'valor': 'aceite', 'tipo': 'articulo'}))
    assert mem.ok, mem.mensaje
    auto = core.orquestador.resolver(SolicitudHostAI('preparar_automatizacion_308', {'texto': 'crea un pedido de aceite para mañana'}))
    assert auto.ok, auto.mensaje
    asist = core.orquestador.resolver(SolicitudHostAI('asistente_host_ai_308', {'texto': 'crea un pedido de aceite para mañana', 'ejecutar': False}))
    assert asist.ok, asist.mensaje
    cierre = core.orquestador.resolver(SolicitudHostAI('comprobar_cierre_ia_conversacional_308', {'ejecutar_pruebas': True}))
    assert cierre.ok, cierre.mensaje
    assert cierre.datos.get('ok_global') is True, cierre.datos.get('incidencias')
    print('TEST OK - Host AI 3.0.8.1 + 3.0.8.2 + 3.0.8.3 + 3.0.8.4 + 3.0.8.5 + 3.0.8.6 + 3.0.8.7 + 3.0.8.8 IA Conversacional')
    print('Intención:', a.datos.get('intencion_detectada'))
    print('Pipeline:', sel.datos.get('pipeline_seleccionado'))
    print('Acción automatizada:', auto.datos.get('accion_detectada'))
    print('Cierre OK:', cierre.datos.get('ok_global'))

if __name__ == '__main__': ejecutar_prueba()
