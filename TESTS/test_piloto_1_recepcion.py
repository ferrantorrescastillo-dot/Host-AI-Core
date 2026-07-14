from pathlib import Path
import json
from SERVICIOS.recepcion_inteligente_piloto_1 import RecepcionInteligentePiloto1

def test_diagnostico(tmp_path):
    base=tmp_path
    (base/'DATOS/db').mkdir(parents=True)
    svc=RecepcionInteligentePiloto1(base)
    out=svc.diagnostico()
    assert out['diagnostico']=='OK'
    assert out['estado']=='COMMIT'
    assert out['stock']==3
    assert out['creados']==1

def test_no_confirma_no_aplica(tmp_path):
    (tmp_path/'DATOS/db').mkdir(parents=True)
    for n,d in {'articulos.json':[], 'stock_lotes.json':[], 'stock_movimientos.json':[], 'precios.json':[], 'proveedores.json':[], 'facturas_piloto.json':[]}.items():
        (tmp_path/'DATOS/db'/n).write_text(json.dumps(d),encoding='utf-8')
    f=tmp_path/'x.csv'; f.write_text('descripcion;cantidad;unidad;precio\nPatata;1;kg;1\n',encoding='utf-8')
    svc=RecepcionInteligentePiloto1(tmp_path)
    plan=svc.preparar(f,proveedor='P')
    svc.actualizar_decision(plan,1,'CREAR',nombre_nuevo='Patata',unidad='kg')
    try: svc.aplicar(plan,'NO')
    except ValueError: pass
    else: assert False
    assert json.loads((tmp_path/'DATOS/db/articulos.json').read_text())==[]

def test_idempotencia(tmp_path):
    (tmp_path/'DATOS/db').mkdir(parents=True)
    for n,d in {'articulos.json':[], 'stock_lotes.json':[], 'stock_movimientos.json':[], 'precios.json':[], 'proveedores.json':[], 'facturas_piloto.json':[]}.items():
        (tmp_path/'DATOS/db'/n).write_text(json.dumps(d),encoding='utf-8')
    f=tmp_path/'x.csv'; f.write_text('descripcion;cantidad;unidad;precio\nPatata;1;kg;1\n',encoding='utf-8')
    svc=RecepcionInteligentePiloto1(tmp_path)
    p=svc.preparar(f,proveedor='P'); svc.actualizar_decision(p,1,'CREAR',nombre_nuevo='Patata',unidad='kg'); svc.aplicar(p,'RECEPCIONAR')
    p2=svc.preparar(f,proveedor='P')
    if p2['lineas'][0]['estado']=='PROBABLE': svc.actualizar_decision(p2,1,'VINCULAR',svc.buscar_articulos('Patata')[0])
    try: svc.aplicar(p2,'RECEPCIONAR')
    except ValueError as e: assert 'anteriormente' in str(e)
    else: assert False
