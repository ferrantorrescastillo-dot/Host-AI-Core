from pathlib import Path
import sys
BASE=Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path: sys.path.insert(0,str(BASE))
from SERVICIOS.clasificador_consultas_datos_551 import clasificar_consulta_datos_551
casos={
'¿Qué menús tienes disponibles en el sistema?':'consultar_menus',
'¿Qué recetas tienes registradas?':'consultar_recetas',
'¿Qué escandallos tienes disponibles?':'consultar_escandallos',
'Busca cualquier receta que contenga arroz':'buscar_catalogo_cocina',
'¿Qué proveedores venden arroz?':'consultar_proveedores',
}
for texto,esperada in casos.items():
    r=clasificar_consulta_datos_551(texto)
    assert r['gestionado'] and r['intencion']==esperada,(texto,r)
print('TEST OK 5.5.1 Clasificador de Consultas de Datos')
