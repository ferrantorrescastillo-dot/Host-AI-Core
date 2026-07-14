from SERVICIOS.constructor_arbol_semantico_menus_i1322 import ConstructorArbolSemanticoMenusI1322
from SERVICIOS.motor_reconocimiento_menus_i1321 import MotorReconocimientoMenusI1321

RECETAS = [
    {"codigo": "R1", "nombre": "Tataki de atún con sésamo"},
    {"codigo": "R2", "nombre": "Solomillo de cerdo"},
    {"codigo": "R3", "nombre": "Salsa naranja"},
    {"codigo": "R4", "nombre": "Parmentier patata"},
]


def constructor(tmp_path, recetas=None, articulos=None):
    motor = MotorReconocimientoMenusI1321(tmp_path, recetas if recetas is not None else RECETAS, articulos or [])
    return ConstructorArbolSemanticoMenusI1322(tmp_path, motor)


def test_i1322_preserva_receta_completa_como_principal(tmp_path):
    r = constructor(tmp_path).construir_texto("Tataki de atún con sésamo")
    assert r["estado_semantico"] == "COMPLETO"
    assert r["arbol"]["receta_principal"]["nombre"] == "Tataki de atún con sésamo"
    assert r["arbol"]["elaboraciones"] == []


def test_i1322_construye_principal_guarnicion_y_salsa_catalogadas(tmp_path):
    r = constructor(tmp_path).construir_texto(
        "Solomillo de cerdo con parmentier patata i salsa naranja"
    )
    a = r["arbol"]
    assert a["receta_principal"]["nombre"] == "Solomillo de cerdo"
    assert [x["nombre"] for x in a["guarniciones"]] == ["Parmentier patata"]
    assert [x["nombre"] for x in a["salsas"]] == ["Salsa naranja"]
    assert r["estado_semantico"] == "COMPLETO"


def test_i1322_conserva_guarnicion_no_catalogada_sin_inventarla(tmp_path):
    recetas = [
        {"codigo": "R2", "nombre": "Solomillo de cerdo"},
        {"codigo": "R3", "nombre": "Salsa naranja"},
    ]
    r = constructor(tmp_path, recetas).construir_texto(
        "Solomillo de cerdo con parmentier patata i salsa naranja"
    )
    a = r["arbol"]
    assert a["receta_principal"]["nombre"] == "Solomillo de cerdo"
    assert a["guarniciones"][0]["nombre"] == "parmentier patata"
    assert a["guarniciones"][0]["catalogado"] is False
    assert a["salsas"][0]["catalogado"] is True
    assert r["estado_semantico"] == "PARCIAL"
    assert r["datos_modificados"] is False


def test_i1322_articulo_completo_no_se_convierte_en_receta(tmp_path):
    r = constructor(tmp_path, [], [{"codigo": "A1", "nombre": "Pan individual rombo makro"}]).construir_texto(
        "Pan individual rombo makro"
    )
    assert r["arbol"]["receta_principal"] is None
    assert r["arbol"]["articulos_directos"][0]["nombre"] == "Pan individual rombo makro"


def test_i1322_no_habilita_importacion(tmp_path):
    r = constructor(tmp_path).construir_texto("Tataki de atún con sésamo")
    assert r["solo_vista_previa"] is True
    assert r["importacion_disponible"] is False
    assert r["datos_modificados"] is False
