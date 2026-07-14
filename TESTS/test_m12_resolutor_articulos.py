import json
from pathlib import Path
import pytest
from CORE.MUR.modelos import ConflictoMUR, TipoEntidad, TipoConflicto, SeveridadConflicto
from SERVICIOS.resolutor_articulos_m12 import ResolutorArticulosM12

@pytest.fixture
def db(tmp_path):
    p=tmp_path/'articulos.json'; p.write_text(json.dumps([
      {'codigo':'ART000001','nombre':'Nuez moscada molida','proveedor':'Makro','familia':'Especias','precio':20.0,'unidad':'kg','activo':True},
      {'codigo':'ART000002','nombre':'Patata Monalisa','proveedor':'Mercabarna','familia':'Verduras','precio':1.2,'unidad':'kg','activo':True}
    ]),encoding='utf-8'); return p

def conflicto(tipo=TipoConflicto.ENTIDAD_NO_EXISTE,nombre='Nuez moscada'):
    return ConflictoMUR('ORG','FLUJO','TEST',TipoEntidad.ARTICULO,tipo,SeveridadConflicto.BLOQUEANTE,nombre,nombre,acciones_permitidas=['VINCULAR','CREAR','EDITAR','MANTENER_PENDIENTE'])

def test_preparar_prioriza_nombre_y_candidatos(db):
    r=ResolutorArticulosM12(db)
    p=r.preparar(conflicto())
    assert p['candidatos'][0]['codigo']=='ART000001'
    assert 'VINCULAR' in p['acciones']

def test_vincular_existente(db):
    r=ResolutorArticulosM12(db)
    out=r.ejecutar(conflicto(),'VINCULAR',{'codigo':'ART000001'})
    assert out.ok and out.datos['articulo']['nombre']=='Nuez moscada molida'
    assert out.aprendizaje_sugerido['entidad_id']=='ART000001'

def test_crear_exige_unidad(db):
    r=ResolutorArticulosM12(db)
    out=r.ejecutar(conflicto(nombre='Cardamomo verde'),'CREAR',{'nombre':'Cardamomo verde','precio':10})
    assert not out.ok and 'unidad' in out.mensaje.lower()

def test_detecta_duplicado_probable(db):
    r=ResolutorArticulosM12(db)
    out=r.ejecutar(conflicto(),'CREAR',{'nombre':'Nuez moscada','unidad':'kg','precio':12})
    assert not out.ok and 'Duplicado probable' in out.mensaje

def test_crear_sin_precio_queda_pendiente_y_hace_backup(db,tmp_path):
    r=ResolutorArticulosM12(db, permitir_sin_precio=True, ruta_backups=tmp_path/'bak')
    out=r.ejecutar(conflicto(nombre='Cardamomo verde'),'CREAR',{'nombre':'Cardamomo verde','unidad':'kg','familia':'Especias'})
    assert out.ok and out.datos['estado_calidad']=='PENDIENTE'
    assert Path(out.datos['backup']).exists()
    data=json.loads(db.read_text()); nuevo=next(x for x in data if x['nombre']=='Cardamomo verde')
    assert nuevo['unidad']=='kg' and nuevo['precio'] is None

def test_politica_puede_bloquear_sin_precio(db):
    r=ResolutorArticulosM12(db, permitir_sin_precio=False)
    out=r.ejecutar(conflicto(nombre='Cardamomo verde'),'CREAR',{'nombre':'Cardamomo verde','unidad':'kg'})
    assert not out.ok

def test_busqueda_por_proveedor_segunda_via(db):
    r=ResolutorArticulosM12(db)
    c=conflicto(nombre='Patata'); c.contexto={'proveedor':'Mercabarna'}
    p=r.preparar(c)
    assert p['candidatos'][0]['codigo']=='ART000002'

def test_editar_completa_precio(db,tmp_path):
    data=json.loads(db.read_text()); data[0]['precio']=None; db.write_text(json.dumps(data),encoding='utf-8')
    r=ResolutorArticulosM12(db,ruta_backups=tmp_path/'b')
    c=conflicto(TipoConflicto.ARTICULO_SIN_PRECIO); c.contexto={'codigo':'ART000001'}
    out=r.ejecutar(c,'EDITAR',{'codigo':'ART000001','precio':22.5})
    assert out.ok and out.datos['estado_calidad']=='COMPLETA'
