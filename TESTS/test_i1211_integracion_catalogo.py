from pathlib import Path
import importlib.util


def _cargar_consola():
    raiz = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('consola_i1211', raiz / 'APP' / 'consola.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_i1211_consola_reutiliza_cargador_catalogo_comun():
    texto = (Path(__file__).resolve().parents[1] / 'APP' / 'consola.py').read_text(encoding='utf-8')
    assert 'catalogo = self._cargar_catalogo_articulos()' in texto
    assert 'Catálogo cargado:' in texto
    assert 'La importación queda bloqueada' in texto


def test_i1211_previa_informa_catalogo_y_motor():
    from SERVICIOS.importador_seguro_escandallos_i12 import formatear_previa_i12
    previa = {
        'resumen': {
            'catalogo_articulos': 354,
            'motor_vinculacion_activo': True,
            'recetas_detectadas': 0,
            'duplicadas': 0,
            'bloqueadas': 0,
            'ingredientes': 0,
            'vinculos_exactos': 0,
            'vinculos_probables': 0,
            'sin_resolver': 0,
        },
        'recetas': [],
    }
    salida = formatear_previa_i12(previa)
    assert 'Catálogo: 354 artículo(s)' in salida
    assert 'Motor: ACTIVO' in salida
