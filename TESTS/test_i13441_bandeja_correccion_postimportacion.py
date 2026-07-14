import json
from pathlib import Path

from SERVICIOS.bandeja_correccion_postimportacion_i13441 import BandejaCorreccionPostimportacionI13441
from SERVICIOS.diagnostico_bandeja_correccion_i13441 import DiagnosticoBandejaCorreccionI13441


def write(root, rel, data):
    p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data),encoding='utf-8');return p


def fixture(tmp_path):
    menus=[{'menu_id':'M1','nombre':'Menu','secciones':[{'seccion_id':'S1','nombre':'Principal'}],
            'platos':[{'plato_id':'P1','nombre':'Plato','seccion':'Postre','componentes':[]}],
            'articulos_directos':[{'nombre':'Pan viejo'}],'bebidas':[],'complementos':[],'servicios':[],
            'economico':{'precio_venta':10,'coste_total':3,'food_cost_pct':99,'beneficio':None},
            'resumen':{'secciones':1,'platos':1,'componentes':0,'articulos_directos':1,'bebidas':0,'complementos':0}}]
    recetas=[{'receta_id':'R1','nombre':'Receta 1'}]
    articulos=[{'codigo':'A1','nombre':'Pan'}]
    write(tmp_path,'menus.json',menus);write(tmp_path,'recetas.json',recetas);write(tmp_path,'articulos.json',articulos)
    return BandejaCorreccionPostimportacionI13441(tmp_path,'menus.json','recetas.json','articulos.json'), recetas, articulos


def idx(b,codigo): return next(i for i,x in enumerate(b.incidencias(),1) if x['codigo']==codigo)


def test_vincular_receta_y_articulo(tmp_path):
    b,rec,art=fixture(tmp_path)
    b.vincular_receta(idx(b,'PLATO_SIN_RECETA_PRINCIPAL'),rec[0])
    b.vincular_articulo(idx(b,'ARTICULO_REFERENCIA_INEXISTENTE'),art[0])
    cod={x['codigo'] for x in b.incidencias()}
    assert 'PLATO_SIN_RECETA_PRINCIPAL' not in cod
    assert 'ARTICULO_REFERENCIA_INEXISTENTE' not in cod


def test_cambiar_seccion_y_recalcular_economia(tmp_path):
    b,_,_=fixture(tmp_path)
    b.cambiar_seccion([idx(b,'SECCION_REFERENCIA_INEXISTENTE')],'Principal')
    b.recalcular_economia()
    cod={x['codigo'] for x in b.incidencias()}
    assert 'SECCION_REFERENCIA_INEXISTENTE' not in cod
    assert 'FOOD_COST_INCOHERENTE' not in cod
    assert 'BENEFICIO_INCOHERENTE' not in cod


def test_eliminar_articulo_inexistente(tmp_path):
    b,_,_=fixture(tmp_path)
    b.eliminar([idx(b,'ARTICULO_REFERENCIA_INEXISTENTE')])
    assert not b.menus[0]['articulos_directos']


def test_no_escribe_antes_de_guardar(tmp_path):
    b,_,_=fixture(tmp_path); p=tmp_path/'menus.json'; antes=p.read_bytes()
    b.recalcular_economia(); assert p.read_bytes()==antes


def test_guardar_commit_backup_y_reauditoria(tmp_path):
    b,rec,art=fixture(tmp_path)
    b.vincular_receta(idx(b,'PLATO_SIN_RECETA_PRINCIPAL'),rec[0])
    b.cambiar_seccion([idx(b,'SECCION_REFERENCIA_INEXISTENTE')],'Principal')
    b.vincular_articulo(idx(b,'ARTICULO_REFERENCIA_INEXISTENTE'),art[0])
    b.recalcular_economia()
    r=b.guardar(confirmar=True)
    assert r['transaccion']['estado']=='COMMIT'
    assert Path(r['transaccion']['backup_dir']).exists()
    assert r['auditoria']['resumen']['errores']==0


def test_diagnostico(tmp_path):
    r=DiagnosticoBandejaCorreccionI13441(tmp_path).ejecutar()
    assert r['diagnostico']=='OK'
    assert r['transaccion']['estado']=='COMMIT'
