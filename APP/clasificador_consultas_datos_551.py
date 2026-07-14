from pathlib import Path
import sys
BASE_DIR=Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0,str(BASE_DIR))
from SERVICIOS.clasificador_consultas_datos_551 import clasificar_consulta_datos_551

if __name__=='__main__':
    print('HOST AI 5.5.1 - CLASIFICADOR DE CONSULTAS DE DATOS')
    for texto in ['¿Qué menús tienes disponibles en el sistema?','¿Qué recetas tienes registradas?','¿Qué escandallos tienes disponibles?']:
        print(texto,'->',clasificar_consulta_datos_551(texto)['intencion'])
