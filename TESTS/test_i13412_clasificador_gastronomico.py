from pathlib import Path

from SERVICIOS.clasificador_gastronomico_i13412 import ClasificadorGastronomicoI13412
from SERVICIOS.simulador_importacion_menus_i13412 import SimuladorImportacionMenusI13412


def _receta(nombre="Pan de cristal con jamón"):
    return [{
        "grupo": "RECETA_PRINCIPAL", "tipo_entidad": "RECETA", "nombre": nombre,
        "catalogado": True, "estado": "EXACTA_COMPLETA"
    }]


def _articulo(nombre="A.P TARTAR"):
    return [{
        "grupo": "ARTICULO_DIRECTO", "tipo_entidad": "ARTICULO", "nombre": nombre,
        "catalogado": True, "estado": "EXACTA_COMPLETA"
    }]


def test_receta_completa_prevalece_sobre_palabra_pan():
    c = ClasificadorGastronomicoI13412().clasificar("Pan de cristal con jamón", _receta())
    assert c.tipo == "PLATO_RECETA"
    assert c.activa_arbol_semantico is True


def test_clasifica_bebidas_y_evitan_arbol_semantico():
    cl = ClasificadorGastronomicoI13412()
    casos = {
        "CLOS PINELL TERRA TINTO ALTA": "VINO",
        "CAVA ROGER DE FLOR": "CAVA",
        "Agua Font Vella 1 LT": "AGUA",
        "Caña de cerveza": "BEBIDA",
        "Cafe Natural 1 kg": "CAFE_INFUSION",
    }
    for texto, esperado in casos.items():
        c = cl.clasificar(texto, _articulo(texto))
        assert c.tipo == esperado
        assert c.activa_arbol_semantico is False


def test_prefijos_ap_mp_son_regla_prioritaria():
    cl = ClasificadorGastronomicoI13412()
    assert cl.clasificar("A.P TARTAR DE SALMON", _articulo()).tipo == "APERITIVO_PREPARADO"
    assert cl.clasificar("M.P PATATA MONALISA", _articulo()).tipo == "MATERIA_PRIMA"


def test_ruido_comercial_no_genera_componentes():
    cl = ClasificadorGastronomicoI13412()
    assert cl.es_ruido_semantico("por pax", "MENU CALÇOTADA")
    assert cl.es_ruido_semantico("menu calcotada", "MENU CALÇOTADA")
    assert not cl.es_ruido_semantico("salsa naranja", "MENU CALÇOTADA")


def test_reclasifica_preimportacion_y_deduplica_secciones(tmp_path: Path):
    sim = SimuladorImportacionMenusI13412(tmp_path)
    pre = {
        "menus": [{
            "nombre": "MENU PRUEBA", "hoja": "MENU PRUEBA",
            "secciones": [{"nombre": "POSTRES"}, {"nombre": "POSTRES"}],
            "platos": [
                {"nombre_original": "Caña de cerveza", "fila": 1, "seccion": "Postre", "componentes": [
                    {"nombre": "cana", "catalogado": False, "grupo": "COMPONENTE_PENDIENTE"},
                    {"nombre": "cerveza", "catalogado": False, "grupo": "COMPONENTE_PENDIENTE"},
                ]},
                {"nombre_original": "Pan de cristal con jamón", "fila": 2, "seccion": "Postre", "componentes": _receta()},
            ],
            "articulos_directos": [], "complementos": [], "economico": {},
        }],
        "bloqueos": [
            {"menu": "MENU PRUEBA", "plato": "Caña de cerveza", "componente": "cana"},
            {"menu": "MENU PRUEBA", "plato": "Caña de cerveza", "componente": "cerveza"},
        ],
    }
    r = sim._clasificar_preimportacion(pre)
    menu = r["menus"][0]
    assert len(menu["secciones"]) == 1
    assert [p["nombre_original"] for p in menu["platos"]] == ["Pan de cristal con jamón"]
    assert [b["nombre"] for b in menu["bebidas"]] == ["Caña de cerveza"]
    assert r["bloqueos"] == []


def test_acciones_no_duplican_ids_con_menus_de_mismo_nombre(tmp_path: Path):
    sim = SimuladorImportacionMenusI13412(tmp_path)
    pre = {
        "menus": [
            {"nombre": "MENU IGUAL", "hoja": "HOJA A", "secciones": [], "platos": [], "articulos_directos": [], "complementos": [], "economico": {}},
            {"nombre": "MENU IGUAL", "hoja": "HOJA B", "secciones": [], "platos": [], "articulos_directos": [], "complementos": [], "economico": {}},
        ],
        "bloqueos": [],
    }
    plan = sim.construir_plan(pre, [])
    ids = [a["accion_id"] for a in plan["acciones"]]
    assert len(ids) == len(set(ids))
