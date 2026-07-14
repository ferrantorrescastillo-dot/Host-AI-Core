from pathlib import Path
import sys
BASE_DIR=Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0,str(BASE_DIR))
from SERVICIOS.consultas_datos_conversacionales_552 import procesar_consulta_datos_552
if __name__=='__main__':
    for q in ['¿Qué menús tienes disponibles en el sistema?','Busca cualquier receta o escandallo que contenga la palabra arroz']:
        print(procesar_consulta_datos_552(q,BASE_DIR)['mensaje'],'\n')
