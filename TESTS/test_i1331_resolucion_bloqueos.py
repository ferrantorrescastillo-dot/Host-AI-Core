from pathlib import Path
import json
import shutil

from SERVICIOS.resolutor_bloqueos_preimportacion_i1331 import ResolutorBloqueosPreimportacionI1331, formatear_resolucion_i1331

BASE = Path(__file__).resolve().parents[1]
EXCEL = Path('/mnt/data/esc_i133/Escandallos Boronat.xlsx')


def _base(tmp_path):
    base = tmp_path / 'host'
    shutil.copytree(BASE / 'DATOS', base / 'DATOS')
    memoria = {'version':'I1.3.2.4','esquema':1,'decisiones':{'parmentier patata':{
        'aprendizaje_id':'CUL-TEST','texto_origen':'parmentier patata','clave_normalizada':'parmentier patata',
        'rol':'GUARNICION','accion':'PROPONER_NUEVA_RECETA','nombre_destino':'Parmentier de patata',
        'tipo_destino':'PROPUESTA_RECETA','entidad_id':'','confianza':1.0,'estado':'ACTIVO','origen':'usuario',
        'usos':0,'creado_en':'x','actualizado_en':'x','ultimo_uso_en':None,'historial':[]}}}
    p=base/'DATOS/db/aprendizaje_culinario_i1324.json'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(memoria),encoding='utf-8')
    return base


def _bloqueo(motor):
    r=motor.recalcular(EXCEL, hojas=['MENU BODA 31-1'])
    assert r['estado_preimportacion']=='BLOQUEADA'
    return r['bloqueos'][0]


def test_vincular_receta_existente_deja_lista(tmp_path):
    motor=ResolutorBloqueosPreimportacionI1331(_base(tmp_path))
    b=_bloqueo(motor)
    rec=motor.buscar_recetas('salsa naranja')[0]
    motor.vincular_receta(b, rec.get('receta_id'))
    r=motor.recalcular(EXCEL, hojas=['MENU BODA 31-1'])
    assert r['estado_preimportacion']=='LISTA'
    assert r['resumen']['bloqueos']==0
    assert r['importacion_disponible'] is False


def test_crear_receta_real_deja_lista_y_hace_backup(tmp_path):
    base=_base(tmp_path); motor=ResolutorBloqueosPreimportacionI1331(base); b=_bloqueo(motor)
    art=motor.buscar_articulos('patata')[0]
    out=motor.crear_receta(b, {'nombre':'Parmentier de patata','raciones_base':10,'ingredientes':[{
        'articulo_id': art.get('id') or art.get('articulo_id'), 'cantidad':2, 'unidad':art.get('unidad','kg')} ]})
    assert Path(out['backup']).exists()
    recetas=json.loads((base/'DATOS/db/escandallos.json').read_text(encoding='utf-8'))
    assert any(x['nombre']=='Parmentier de patata' and x['lineas'] for x in recetas)
    r=motor.recalcular(EXCEL, hojas=['MENU BODA 31-1'])
    assert r['estado_preimportacion']=='LISTA'
    assert r['resumen']['bloqueos']==0


def test_no_permite_receta_sin_ingredientes(tmp_path):
    motor=ResolutorBloqueosPreimportacionI1331(_base(tmp_path)); b=_bloqueo(motor)
    try:
        motor.crear_receta(b, {'nombre':'Parmentier de patata','raciones_base':10,'ingredientes':[]})
    except ValueError as exc:
        assert 'al menos un ingrediente' in str(exc)
    else:
        raise AssertionError('Debió bloquear la receta incompleta')


def test_formato_indica_importacion_deshabilitada(tmp_path):
    motor=ResolutorBloqueosPreimportacionI1331(_base(tmp_path))
    texto=formatear_resolucion_i1331(motor.recalcular(EXCEL, hojas=['MENU BODA 31-1']))
    assert 'I1.3.3.1' in texto
    assert 'nunca importa el menú' in texto
    assert 'ESTADO FINAL: BLOQUEADA' in texto
