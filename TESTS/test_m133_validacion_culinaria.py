from pathlib import Path
import json, tempfile

from SERVICIOS.importador_inteligente_recetas_m131 import ImportadorInteligenteRecetasM131
from SERVICIOS.validacion_culinaria_m133 import ValidadorCulinarioM133


def catalogo(p: Path):
    f=p/'articulos.json'
    f.write_text(json.dumps([
        {'codigo':'M.P-PAT','nombre':'Patata','unidad':'kg','precio':1.2},
        {'codigo':'M.P-MANT','nombre':'Mantequilla','unidad':'kg','precio':8},
        {'codigo':'M.P-LECHE','nombre':'Leche','unidad':'l','precio':1.1},
        {'codigo':'M.P-NUEZ','nombre':'Nuez moscada','unidad':'kg','precio':None},
        {'codigo':'A.P-BRIOX','nombre':'A.P Briox de curri','unidad':'ud','precio':3},
    ]),encoding='utf-8')
    return f


def receta(cat, texto=None):
    texto=texto or 'Parmentier\nRendimiento: 10\nIngredientes\n2 kg Patata\n0.25 kg Mantequilla\n0.5 l Leche\nElaboración\nCocer 25 min. Conservar refrigerado 48 h.'
    return ImportadorInteligenteRecetasM131(cat).desde_texto(texto)


def test_receta_coherente_sin_errores():
    with tempfile.TemporaryDirectory() as d:
        cat=catalogo(Path(d)); r=ValidadorCulinarioM133(cat).validar(receta(cat),metadatos={'alergenos':['LECHE'],'tiempos':'25 min','conservacion':'48 h'})
        assert r.errores==0 and r.estado=='VALIDADA'


def test_rendimiento_cero_bloquea():
    with tempfile.TemporaryDirectory() as d:
        cat=catalogo(Path(d)); b=receta(cat,'X\nRendimiento: 0\nIngredientes\n1 kg Patata\nElaboración\nCocer.'); r=ValidadorCulinarioM133(cat).validar(b)
        assert any(x.codigo=='RENDIMIENTO_INVALIDO' for x in r.hallazgos) and r.bloqueada


def test_cantidad_cero_bloquea():
    with tempfile.TemporaryDirectory() as d:
        cat=catalogo(Path(d)); b=receta(cat,'X\nRendimiento: 1\nIngredientes\n0 kg Patata\nElaboración\nCocer.'); r=ValidadorCulinarioM133(cat).validar(b)
        assert any(x.codigo=='CANTIDAD_NO_POSITIVA' for x in r.hallazgos)


def test_duplicado_es_aviso_no_error():
    with tempfile.TemporaryDirectory() as d:
        cat=catalogo(Path(d)); b=receta(cat,'X\nRendimiento: 1\nIngredientes\n1 kg Patata\n0.5 kg Patata\nElaboración\nCocer 10 min. Conservar frío.'); r=ValidadorCulinarioM133(cat).validar(b,metadatos={'alergenos':['NINGUNO']})
        assert any(x.codigo=='INGREDIENTE_DUPLICADO' and x.severidad=='AVISO' for x in r.hallazgos)


def test_mantequilla_en_litros_es_aviso():
    with tempfile.TemporaryDirectory() as d:
        cat=catalogo(Path(d)); b=receta(cat,'X\nRendimiento: 1\nIngredientes\n2 l Mantequilla\nElaboración\nFundir 10 min. Conservar frío.'); r=ValidadorCulinarioM133(cat).validar(b,metadatos={'alergenos':['LECHE']})
        assert any(x.codigo=='UNIDAD_SOSPECHOSA_SOLIDO' for x in r.hallazgos)


def test_ap_como_materia_prima_bloquea():
    with tempfile.TemporaryDirectory() as d:
        cat=catalogo(Path(d)); b=receta(cat,'X\nRendimiento: 1\nIngredientes\n1 ud Briox de curri\nElaboración\nServir.'); ing=b.ingredientes[0]
        ing.articulo_id='A.P-BRIOX';ing.clase_articulo='APERITIVO';ing.estado='VINCULADO'
        r=ValidadorCulinarioM133(cat).validar(b)
        assert any(x.codigo=='AP_COMO_MATERIA_PRIMA' and x.severidad=='ERROR' for x in r.hallazgos)


def test_precio_faltante_avisa_y_coste_parcial():
    with tempfile.TemporaryDirectory() as d:
        cat=catalogo(Path(d)); b=receta(cat,'X\nRendimiento: 10\nIngredientes\n1 kg Patata\n0.01 kg Nuez moscada\nElaboración\nCocer 10 min. Conservar frío.'); r=ValidadorCulinarioM133(cat).validar(b,metadatos={'alergenos':['NINGUNO']})
        assert any(x.codigo=='COSTE_INCOMPLETO' for x in r.hallazgos) and r.errores==0


def test_falta_elaboracion_tiempos_conservacion_alergenos_son_avisos():
    with tempfile.TemporaryDirectory() as d:
        cat=catalogo(Path(d)); b=receta(cat,'X\nRendimiento: 1\nIngredientes\n1 kg Patata'); r=ValidadorCulinarioM133(cat).validar(b)
        codigos={x.codigo for x in r.hallazgos}
        assert {'SIN_ELABORACION','SIN_TIEMPOS','SIN_CONSERVACION','ALERGENOS_NO_REVISADOS'} <= codigos
