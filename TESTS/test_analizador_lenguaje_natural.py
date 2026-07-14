from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    r = core.orquestador.resolver(SolicitudHostAI('analizar_lenguaje_natural', {'texto': '¿Qué debería comprar mañana si me queda poco aceite y arroz?'}))
    assert r.ok, r.mensaje
    assert r.datos['version'] == '3.0.8.1'
    assert r.datos['intencion_detectada'] in ('consulta_compras','consulta_stock')
    assert len(r.datos['entidades']) >= 2
    assert r.datos['pipeline_sugerido']
    print('TEST OK - Host AI 3.0.8.1 Analizador de Lenguaje Natural')
    print('Intención:', r.datos['intencion_detectada'])
    print('Entidades:', len(r.datos['entidades']))

if __name__ == '__main__': ejecutar_prueba()
