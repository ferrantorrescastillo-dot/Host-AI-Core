from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    r = core.orquestador.resolver(SolicitudHostAI('comprobar_cierre_ia_conversacional_308', {'ejecutar_pruebas': True}))
    assert r.ok, r.mensaje
    assert r.datos.get('version') == '3.0.8.8'
    assert r.datos.get('ok_global') is True, r.datos.get('incidencias')
    assert r.datos.get('metricas', {}).get('modulos_validados', 0) >= 7
    print('TEST OK - Host AI 3.0.8.8 Cierre IA Conversacional')
    print('Módulos validados:', r.datos.get('metricas', {}).get('modulos_validados'))

if __name__ == '__main__': ejecutar_prueba()
