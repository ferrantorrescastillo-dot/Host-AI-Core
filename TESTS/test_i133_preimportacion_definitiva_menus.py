from pathlib import Path
import json
import shutil

from SERVICIOS.preimportador_definitivo_menus_i133 import PreimportadorDefinitivoMenusI133, formatear_preimportacion_i133

BASE = Path(__file__).resolve().parents[1]
EXCEL = Path('/mnt/data/esc_i133/Escandallos Boronat.xlsx')


def _motor_con_memoria(tmp_path):
    # Copia solo los datos necesarios para no tocar el proyecto.
    base = tmp_path / 'host'
    shutil.copytree(BASE / 'DATOS', base / 'DATOS')
    memoria = {
        'version':'I1.3.2.4','esquema':1,'decisiones':{
            'parmentier patata': {
                'aprendizaje_id':'CUL-TEST','texto_origen':'parmentier patata','clave_normalizada':'parmentier patata',
                'rol':'GUARNICION','accion':'PROPONER_NUEVA_RECETA','nombre_destino':'Parmentier de patata',
                'tipo_destino':'PROPUESTA_RECETA','entidad_id':'','confianza':1.0,'estado':'ACTIVO','origen':'usuario',
                'usos':0,'creado_en':'x','actualizado_en':'x','ultimo_uso_en':None,'historial':[]
            }
        }
    }
    ruta = base / 'DATOS/db/aprendizaje_culinario_i1324.json'
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(memoria), encoding='utf-8')
    return PreimportadorDefinitivoMenusI133(base)


def test_preimportacion_bloqueada_por_receta_propuesta(tmp_path):
    r = _motor_con_memoria(tmp_path).preparar(EXCEL, hojas=['MENU BODA 31-1'])
    assert r['estado_preimportacion'] == 'BLOQUEADA'
    assert r['importacion_disponible'] is False
    assert r['datos_modificados'] is False
    assert len(r['bloqueos']) == 1
    assert r['bloqueos'][0]['codigo'] == 'RECETA_PROPUESTA_NO_CREADA'
    assert r['bloqueos'][0]['componente'] == 'Parmentier de patata'


def test_contrato_contiene_menu_economia_y_componentes(tmp_path):
    r = _motor_con_memoria(tmp_path).preparar(EXCEL, hojas=['MENU BODA 31-1'])
    m = r['menus'][0]
    assert len(m['platos']) == 12
    assert len(m['articulos_directos']) == 1
    assert len(m['complementos']) == 1
    assert round(m['economico']['precio_venta'], 2) == 75.00
    assert round(m['economico']['coste_total'], 4) == 8.8680
    sol = next(p for p in m['platos'] if p['nombre_original'].startswith('Solomillo'))
    nombres = [c['nombre'] for c in sol['componentes']]
    assert 'Solomillo de cerdo' in nombres
    assert 'Parmentier de patata' in nombres
    assert 'Salsa naranja' in nombres


def test_formato_explica_bloqueo(tmp_path):
    r = _motor_con_memoria(tmp_path).preparar(EXCEL, hojas=['MENU BODA 31-1'])
    texto = formatear_preimportacion_i133(r)
    assert 'IMPORTACIÓN BLOQUEADA' in texto
    assert 'Parmentier de patata' in texto
    assert 'SOLO PREIMPORTACIÓN' in texto
