import json
from pathlib import Path

from SERVICIOS.auditor_integridad_postimportacion_i1344 import AuditorIntegridadPostimportacionI1344
from SERVICIOS.diagnostico_auditoria_postimportacion_i1344 import DiagnosticoAuditoriaPostimportacionI1344


def write(root, rel, data):
    p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(data), encoding='utf-8'); return p


def fixture_valida(tmp_path):
    menus=[{'menu_id':'M1','nombre':'Menu 1','secciones':[{'seccion_id':'S1','nombre':'Principal'}],
      'platos':[{'plato_id':'P1','nombre':'Plato 1','seccion':'Principal','componentes':[{'componente_id':'C1','rol':'RECETA_PRINCIPAL','nombre':'Receta 1','plato_id':'P1'}]}],
      'articulos_directos':[{'nombre':'Pan'}],'bebidas':[],'complementos':[],'servicios':[],
      'economico':{'precio_venta':10,'coste_total':3,'food_cost_pct':30,'beneficio':7},
      'resumen':{'secciones':1,'platos':1,'componentes':1,'articulos_directos':1,'bebidas':0,'complementos':0}}]
    write(tmp_path,'menus.json',menus);write(tmp_path,'recetas.json',[{'receta_id':'R1','nombre':'Receta 1'}]);write(tmp_path,'articulos.json',[{'codigo':'A1','nombre':'Pan'}])
    return AuditorIntegridadPostimportacionI1344(tmp_path,'menus.json','recetas.json','articulos.json','informes')


def test_certifica_catalogo_valido(tmp_path):
    r=fixture_valida(tmp_path).auditar(); assert r['estado']=='CERTIFICADA'; assert r['resumen']['errores']==0


def test_detecta_componente_huerfano_y_receta_inexistente(tmp_path):
    aud=fixture_valida(tmp_path); p=tmp_path/'menus.json'; d=json.loads(p.read_text()); c=d[0]['platos'][0]['componentes'][0]; c['plato_id']='OTRO'; c['nombre']='No existe'; p.write_text(json.dumps(d))
    r=aud.auditar(); codigos={x['codigo'] for x in r['incidencias']}; assert 'COMPONENTE_PLATO_ID_INCORRECTO' in codigos; assert 'RECETA_REFERENCIA_INEXISTENTE' in codigos; assert r['estado']=='NO_CERTIFICADA'


def test_detecta_duplicados(tmp_path):
    aud=fixture_valida(tmp_path); p=tmp_path/'menus.json'; d=json.loads(p.read_text()); d.append(d[0].copy()); p.write_text(json.dumps(d))
    r=aud.auditar(); assert any(x['codigo']=='MENU_ID_DUPLICADO' for x in r['incidencias'])


def test_detecta_economia_incoherente_sin_modificar_menu(tmp_path):
    aud=fixture_valida(tmp_path); p=tmp_path/'menus.json'; d=json.loads(p.read_text()); d[0]['economico']['food_cost_pct']=99; p.write_text(json.dumps(d)); antes=p.read_bytes()
    r=aud.auditar(); assert any(x['codigo']=='FOOD_COST_INCOHERENTE' for x in r['incidencias']); assert p.read_bytes()==antes


def test_diagnostico_aislado(tmp_path):
    r=DiagnosticoAuditoriaPostimportacionI1344(tmp_path).ejecutar(); assert r['diagnostico']=='OK'; assert Path(r['informe_json']).exists()
