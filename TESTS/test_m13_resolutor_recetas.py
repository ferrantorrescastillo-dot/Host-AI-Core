from pathlib import Path
import json
import tempfile

from CORE.MUR.modelos import ConflictoMUR, TipoEntidad, TipoConflicto, SeveridadConflicto
from SERVICIOS.resolutor_recetas_m13 import ResolutorRecetasM13


def preparar(tmp: Path):
    recetas = tmp/'recetas.json'; articulos = tmp/'articulos.json'
    recetas.write_text(json.dumps([{
        'receta_id':'REC-SALSA','nombre':'Salsa naranja','raciones_base':10,
        'lineas':[{'articulo_id':'ART1','cantidad':1,'unidad':'kg'}],'activo':True
    }]),encoding='utf-8')
    articulos.write_text(json.dumps([{'codigo':'ART1','nombre':'Patata','unidad':'kg','precio':2.0}]),encoding='utf-8')
    return recetas, articulos


def conflicto(nombre='Parmentier de patata'):
    return ConflictoMUR('ORG','FLUJO','TEST',TipoEntidad.RECETA,TipoConflicto.ENTIDAD_NO_EXISTE,SeveridadConflicto.BLOQUEANTE,nombre,nombre)


def test_soporta_recetas():
    with tempfile.TemporaryDirectory() as d:
        r,a=preparar(Path(d)); res=ResolutorRecetasM13(r,a)
        assert res.soporta(conflicto())


def test_busqueda_exacta():
    with tempfile.TemporaryDirectory() as d:
        r,a=preparar(Path(d)); res=ResolutorRecetasM13(r,a)
        halladas=res.buscar_recetas('Salsa naranja')
        assert halladas and halladas[0]['puntuacion']==1.0


def test_creacion_exige_rendimiento():
    with tempfile.TemporaryDirectory() as d:
        r,a=preparar(Path(d)); res=ResolutorRecetasM13(r,a)
        out=res.ejecutar(conflicto(),'CREAR',{'nombre':'Parmentier','ingredientes':[{'articulo_id':'ART1','cantidad':1,'unidad':'kg'}]})
        assert not out.ok


def test_creacion_exige_ingredientes():
    with tempfile.TemporaryDirectory() as d:
        r,a=preparar(Path(d)); res=ResolutorRecetasM13(r,a)
        out=res.ejecutar(conflicto(),'CREAR',{'nombre':'Parmentier','raciones_base':10,'ingredientes':[]})
        assert not out.ok


def test_ingrediente_debe_existir():
    with tempfile.TemporaryDirectory() as d:
        r,a=preparar(Path(d)); res=ResolutorRecetasM13(r,a)
        out=res.ejecutar(conflicto(),'CREAR',{'nombre':'Parmentier','raciones_base':10,'ingredientes':[{'articulo_id':'NO','cantidad':1,'unidad':'kg'}]})
        assert not out.ok


def test_evitar_duplicado():
    with tempfile.TemporaryDirectory() as d:
        r,a=preparar(Path(d)); res=ResolutorRecetasM13(r,a)
        out=res.ejecutar(conflicto('Salsa naranja'),'CREAR',{'nombre':'Salsa naranja','raciones_base':10,'ingredientes':[{'articulo_id':'ART1','cantidad':1,'unidad':'kg'}]})
        assert not out.ok and out.datos.get('duplicados')


def test_crear_receta_completa_y_backup():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d); r,a=preparar(p); res=ResolutorRecetasM13(r,a,p/'backups')
        out=res.ejecutar(conflicto(),'CREAR',{'nombre':'Parmentier de patata','raciones_base':10,'ingredientes':[{'articulo_id':'ART1','cantidad':2,'unidad':'kg'}]})
        assert out.ok
        assert out.datos['estado_calidad']=='COMPLETA'
        assert out.datos['receta']['coste_por_racion']==0.4
        assert Path(out.datos['backup']).exists()


def test_vincular_receta_completa():
    with tempfile.TemporaryDirectory() as d:
        r,a=preparar(Path(d)); res=ResolutorRecetasM13(r,a)
        out=res.ejecutar(conflicto('Salsa'),'VINCULAR',{'receta_id':'REC-SALSA'})
        assert out.ok and out.aprendizaje_sugerido['tipo_entidad']=='RECETA'
