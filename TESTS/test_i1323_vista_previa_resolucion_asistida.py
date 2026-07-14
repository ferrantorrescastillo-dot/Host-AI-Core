from pathlib import Path
import json

from SERVICIOS.vista_previa_resolucion_asistida_menus_i1323 import VistaPreviaResolucionAsistidaMenusI1323

BASE = Path(__file__).resolve().parents[1]
EXCEL = Path('/mnt/data/esc_test/Escandallos Boronat.xlsx')


def test_previa_real_detecta_un_pendiente_y_no_importa(tmp_path):
    asistente = VistaPreviaResolucionAsistidaMenusI1323(BASE)
    asistente.ruta_memoria = tmp_path / 'memoria.json'
    asistente.memoria = {}
    r = asistente.preparar_desde_excel(EXCEL, hojas=['MENU BODA 31-1'])
    assert r['resumen']['platos'] == 12
    assert r['resumen_resolucion']['pendientes_revision'] == 1
    assert r['pendientes_revision'][0]['texto'] == 'parmentier patata'
    assert r['importacion_disponible'] is False
    assert r['datos_modificados'] is False
    assert not asistente.ruta_memoria.exists()


def test_vincular_receta_solo_modifica_previa(tmp_path):
    asistente = VistaPreviaResolucionAsistidaMenusI1323(BASE)
    asistente.ruta_memoria = tmp_path / 'memoria.json'; asistente.memoria = {}
    r = asistente.preparar_desde_excel(EXCEL, hojas=['MENU BODA 31-1'])
    ok = asistente.aplicar_decision(r, 'parmentier patata', 'GUARNICION', 'VINCULAR_RECETA', {
        'nombre':'Parmentier de patata', 'tipo':'RECETA', 'entidad_id':'REC-PARMENTIER'
    }, recordar=False)
    assert ok is True
    assert r['resumen_resolucion']['pendientes_revision'] == 0
    assert not asistente.ruta_memoria.exists()
    plato = next(p for m in r['menus'] for p in m['platos'] if p['nombre'].startswith('Solomillo'))
    guarnicion = plato['semantica']['arbol']['guarniciones'][0]
    assert guarnicion['nombre'] == 'Parmentier de patata'
    assert guarnicion['catalogado'] is True
    assert guarnicion['resolucion'] == 'VINCULAR_RECETA'


def test_propuesta_nueva_receta_no_crea_catalogo(tmp_path):
    asistente = VistaPreviaResolucionAsistidaMenusI1323(BASE)
    asistente.ruta_memoria = tmp_path / 'memoria.json'; asistente.memoria = {}
    r = asistente.preparar_desde_excel(EXCEL, hojas=['MENU BODA 31-1'])
    before = len(asistente.motor.recetas)
    asistente.aplicar_decision(r, 'parmentier patata', 'GUARNICION', 'PROPONER_NUEVA_RECETA', {
        'nombre':'Parmentier de patata', 'tipo':'PROPUESTA_RECETA'
    }, recordar=False)
    assert len(asistente.motor.recetas) == before
    assert not asistente.ruta_memoria.exists()


def test_recordar_decision_requiere_llamada_explicita_y_se_reutiliza(tmp_path):
    asistente = VistaPreviaResolucionAsistidaMenusI1323(BASE)
    asistente.ruta_memoria = tmp_path / 'memoria.json'; asistente.memoria = {}
    r = asistente.preparar_desde_excel(EXCEL, hojas=['MENU BODA 31-1'])
    asistente.aplicar_decision(r, 'parmentier patata', 'GUARNICION', 'VINCULAR_RECETA', {
        'nombre':'Parmentier de patata', 'tipo':'RECETA', 'entidad_id':'REC-PARMENTIER'
    }, recordar=True)
    assert asistente.ruta_memoria.exists()
    data = json.loads(asistente.ruta_memoria.read_text(encoding='utf-8'))
    assert 'parmentier patata' in data
    nuevo = VistaPreviaResolucionAsistidaMenusI1323(BASE)
    nuevo.ruta_memoria = asistente.ruta_memoria
    nuevo.memoria = nuevo._cargar_memoria()
    r2 = nuevo.preparar_desde_excel(EXCEL, hojas=['MENU BODA 31-1'])
    assert r2['resumen_resolucion']['pendientes_revision'] == 0
    assert r2['resumen_resolucion']['decisiones_recordadas_aplicadas'] == 1


def test_candidatos_devuelve_recetas_y_articulos():
    asistente = VistaPreviaResolucionAsistidaMenusI1323(BASE)
    c = asistente.candidatos('parmentier patata')
    assert 'recetas' in c and 'articulos' in c
    assert len(c['recetas']) <= 8 and len(c['articulos']) <= 8
