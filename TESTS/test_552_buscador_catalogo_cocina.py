from pathlib import Path
import sys,tempfile,json
BASE=Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path: sys.path.insert(0,str(BASE))
from SERVICIOS.consultas_datos_conversacionales_552 import procesar_consulta_datos_552
with tempfile.TemporaryDirectory() as d:
    b=Path(d); (b/'DATOS/db').mkdir(parents=True)
    (b/'DATOS/db/escandallos.json').write_text(json.dumps([{'nombre':'Paella de marisco'},{'nombre':'Arroz negro'}]),encoding='utf-8')
    (b/'DATOS/db/articulos.json').write_text(json.dumps([{'nombre':'Arroz bomba'}]),encoding='utf-8')
    (b/'DATOS/db/proveedores.json').write_text(json.dumps([{'nombre':'Makro'}]),encoding='utf-8')
    r=procesar_consulta_datos_552('¿Qué recetas tienes registradas?',b)
    assert r['gestionado'] and 'Paella de marisco' in r['mensaje']
    r=procesar_consulta_datos_552('Busca cualquier receta o escandallo que contenga la palabra arroz',b)
    assert r['datos']['total']>=2
print('TEST OK 5.5.2 Buscador de Menus Recetas y Escandallos')
