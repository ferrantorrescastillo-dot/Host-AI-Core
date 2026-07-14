from pathlib import Path
import json, tempfile

from SERVICIOS.importador_inteligente_recetas_m131 import ImportadorInteligenteRecetasM131
from SERVICIOS.resolucion_ingredientes_m132 import ResolucionIngredientesM132


def preparar(p: Path):
    f=p/'articulos.json'
    f.write_text(json.dumps([
      {'codigo':'M.P-PAT','nombre':'Patata','unidad':'kg','precio':1},
      {'codigo':'A.P-BRIOX','nombre':'A.P Briox de curri','unidad':'ud','precio':3},
    ]),encoding='utf-8')
    return f


def borrador(cat):
    return ImportadorInteligenteRecetasM131(cat).desde_texto(
      'Parmentier\nRendimiento: 10\nIngredientes\n2 kg Patata\n0.5 l Leche\n0.01 kg Nuez moscada\nElaboración\nCocer.')


def test_construye_cola_solo_no_resueltos():
    with tempfile.TemporaryDirectory() as d:
        cat=preparar(Path(d)); b=borrador(cat); g=ResolucionIngredientesM132(cat)
        cola=g.construir_cola(b)
        assert [x.ingrediente for x in cola]==['Leche','Nuez moscada']


def test_resuelve_dos_conflictos_anidados_y_reanuda():
    with tempfile.TemporaryDirectory() as d:
        cat=preparar(Path(d)); b=borrador(cat); g=ResolucionIngredientesM132(cat)
        r=g.resolver(b, decisiones={
          'Leche':{'accion':'CREAR','payload':{'unidad':'l','precio':1.1}},
          'Nuez moscada':{'accion':'CREAR','payload':{'unidad':'kg','precio':None}},
        })
        assert r.conflictos_creados==2 and r.conflictos_cerrados==2
        assert not r.bloqueos_finales
        assert all(x.estado=='RESUELTO' for x in r.cola)


def test_articulo_sin_precio_queda_pendiente_pero_no_bloquea():
    with tempfile.TemporaryDirectory() as d:
        cat=preparar(Path(d)); b=borrador(cat); g=ResolucionIngredientesM132(cat, permitir_sin_precio=True)
        r=g.resolver(b, decisiones={
          'Leche':{'accion':'CREAR','payload':{'unidad':'l','precio':1.1}},
          'Nuez moscada':{'accion':'CREAR','payload':{'unidad':'kg'}},
        })
        data=json.loads(cat.read_text())
        nuez=next(x for x in data if x.get('nombre')=='Nuez moscada')
        assert nuez.get('estado_calidad')=='PENDIENTE' and not r.bloqueos_finales


def test_sin_decision_conserva_bloqueo_y_checkpoint():
    with tempfile.TemporaryDirectory() as d:
        cat=preparar(Path(d)); b=borrador(cat); g=ResolucionIngredientesM132(cat)
        r=g.resolver(b, decisiones={})
        assert r.bloqueos_finales and all(x.checkpoint_id for x in r.cola)
        assert all(x.estado=='PENDIENTE_USUARIO' for x in r.cola)


def test_no_usa_ap_como_materia_prima():
    with tempfile.TemporaryDirectory() as d:
        cat=preparar(Path(d)); imp=ImportadorInteligenteRecetasM131(cat)
        b=imp.desde_texto('X\nRendimiento: 1\nIngredientes\n1 ud Briox de curri')
        assert not b.ingredientes[0].articulo_id


def test_payload_final_valido():
    with tempfile.TemporaryDirectory() as d:
        cat=preparar(Path(d)); imp=ImportadorInteligenteRecetasM131(cat); b=borrador(cat)
        r=ResolucionIngredientesM132(cat).resolver(b, decisiones={
          'Leche':{'accion':'CREAR','payload':{'unidad':'l','precio':1}},
          'Nuez moscada':{'accion':'CREAR','payload':{'unidad':'kg','precio':20}},
        })
        payload=imp.payload_creacion(r.borrador)
        assert len(payload['ingredientes'])==3
