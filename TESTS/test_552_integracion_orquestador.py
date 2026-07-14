from pathlib import Path
import sys,tempfile,json
BASE=Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path: sys.path.insert(0,str(BASE))
from SERVICIOS.orquestador_inteligente_52 import OrquestadorInteligente52
with tempfile.TemporaryDirectory() as d:
    b=Path(d); (b/'DATOS/db').mkdir(parents=True)
    for f,data in [('escandallos.json',[{'nombre':'Paella de marisco'}]),('articulos.json',[]),('proveedores.json',[])]:
        (b/'DATOS/db'/f).write_text(json.dumps(data),encoding='utf-8')
    o=OrquestadorInteligente52(b)
    r=o.procesar('¿Qué menús tienes disponibles en el sistema?')
    assert r['intencion']=='consultar_menus' and 'Paella de marisco' in r['mensaje']
print('TEST OK 5.5.2 Integracion Conversacional de Datos')
