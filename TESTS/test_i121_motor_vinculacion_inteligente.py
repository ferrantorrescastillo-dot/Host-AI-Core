from types import SimpleNamespace
from SERVICIOS.importador_seguro_escandallos_i12 import ImportadorSeguroEscandallosI12, _norm


def motor():
    return ImportadorSeguroEscandallosI12()


def test_normaliza_formatos_envases_y_acentos():
    assert _norm('Ajo rojo pelado. pqt 1 kg.') == 'ajo'
    assert _norm('ACEITE DE OLIVA SUAVE 5 LT') == 'aceite oliva suave'
    assert _norm('Mayonesa 2,2kg') == 'mayonesa'


def test_vincula_descripciones_largas_con_articulo_corto():
    imp = motor()
    catalogo = imp._catalogo([
        {'id': 'ART-1', 'nombre': 'Ajo rojo pelado'},
        {'id': 'ART-2', 'nombre': 'Aceite de oliva suave'},
        {'id': 'ART-3', 'nombre': 'Mayonesa'},
        {'id': 'ART-4', 'nombre': 'Menta'},
    ])
    casos = [
        ('Ajo rojo pelado. pqt 1 kg.', 'ART-1'),
        ('ACEITE DE OLIVA SUAVE 5 LT', 'ART-2'),
        ('Mayonesa 2,2kg', 'ART-3'),
        ('menta manojo de 100 gr. 1,20€ manojo.', 'ART-4'),
    ]
    for nombre, esperado in casos:
        r = imp._vincular(SimpleNamespace(nombre=nombre, cantidad=1, unidad='kg', precio_unitario=1, coste=1, avisos=[]), catalogo)
        assert r.articulo_id == esperado
        assert r.estado == 'exacto'


def test_reconoce_sinonimos_catalan_castellano():
    imp = motor()
    catalogo = imp._catalogo([
        {'id': 'ART-CARR', 'nombre': 'Carrillera de cerdo'},
        {'id': 'ART-ALC', 'nombre': 'Alcachofa confitada'},
        {'id': 'ART-TOM', 'nombre': 'Tomate pera'},
    ])
    for nombre, esperado in [('Galtes porc', 'ART-CARR'), ('Carxofa confitada flor', 'ART-ALC'), ('Tomate Pera.', 'ART-TOM')]:
        r = imp._vincular(SimpleNamespace(nombre=nombre, cantidad=1, unidad='kg', precio_unitario=1, coste=1, avisos=[]), catalogo)
        assert r.articulo_id == esperado
        assert r.estado in {'exacto', 'probable'}


def test_ambiguedad_se_marca_probable():
    imp = motor()
    catalogo = imp._catalogo([
        {'id': 'A', 'nombre': 'Queso azul vaca'},
        {'id': 'B', 'nombre': 'Queso azul cabra'},
    ])
    r = imp._vincular(SimpleNamespace(nombre='Queso azul', cantidad=1, unidad='kg', precio_unitario=1, coste=1, avisos=[]), catalogo)
    assert r.estado == 'probable'
    assert len(r.candidatos) == 2


def test_no_fuerza_vinculo_sin_similitud_suficiente():
    imp = motor()
    catalogo = imp._catalogo([{'id': 'A', 'nombre': 'Arroz bomba'}])
    r = imp._vincular(SimpleNamespace(nombre='Flor de hibiscus', cantidad=1, unidad='kg', precio_unitario=1, coste=1, avisos=[]), catalogo)
    assert r.estado == 'sin_resolver'
    assert r.articulo_id == ''
