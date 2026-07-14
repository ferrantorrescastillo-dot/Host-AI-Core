import json
from pathlib import Path

from openpyxl import Workbook

from SERVICIOS.motor_reconocimiento_menus_i1321 import MotorReconocimientoMenusI1321


RECETAS = [
    {"codigo": "R1", "nombre": "Tataki de atún con sésamo"},
    {"codigo": "R2", "nombre": "Solomillo de cerdo"},
    {"codigo": "R3", "nombre": "Parmentier patata"},
    {"codigo": "R4", "nombre": "Salsa naranja"},
    {"codigo": "R5", "nombre": "Ceviche de corvina"},
]
ARTICULOS = [
    {"codigo": "A1", "nombre": "Pan individual rombo makro"},
    {"codigo": "A2", "nombre": "Sésamo"},
]


def test_i1321_preserva_receta_completa_sin_fragmentarla(tmp_path):
    motor = MotorReconocimientoMenusI1321(tmp_path, RECETAS, ARTICULOS)
    resultado = motor.reconocer_texto("Tataki de atún con sésamo")
    assert resultado["modo"] == "RECETA_COMPLETA"
    assert len(resultado["coincidencias"]) == 1
    assert resultado["coincidencias"][0]["entidad_id"] == "R1"
    assert resultado["tokens_sin_resolver"] == []


def test_i1321_crea_mapa_de_entidades_sin_interpretar(tmp_path):
    motor = MotorReconocimientoMenusI1321(tmp_path, RECETAS, ARTICULOS)
    resultado = motor.reconocer_texto("Solomillo de cerdo con parmentier patata i salsa naranja")
    assert resultado["modo"] == "MAPA_PARCIAL"
    assert [x["entidad_id"] for x in resultado["coincidencias"]] == ["R2", "R3", "R4"]
    assert resultado["interpretacion_semantica"] is False
    assert resultado["tokens_sin_resolver"] == ["con", "i"]


def test_i1321_reconoce_articulo_directo(tmp_path):
    motor = MotorReconocimientoMenusI1321(tmp_path, RECETAS, ARTICULOS)
    resultado = motor.reconocer_texto("Pan individual rombo makro")
    assert resultado["coincidencias"][0]["tipo"] == "ARTICULO"
    assert resultado["coincidencias"][0]["estado"] == "EXACTA_COMPLETA"


def test_i1321_carga_catalogo_real_sin_escribir(tmp_path):
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True)
    recetas_path = db / "escandallos_canonicos.json"
    articulos_path = db / "articulos.json"
    recetas_path.write_text(json.dumps({"escandallos": RECETAS}, ensure_ascii=False), encoding="utf-8")
    articulos_path.write_text(json.dumps({"articulos": ARTICULOS}, ensure_ascii=False), encoding="utf-8")
    motor = MotorReconocimientoMenusI1321(tmp_path)
    antes = motor.huellas_fuentes()
    resultado = motor.reconocer_texto("Ceviche de corvina")
    despues = motor.huellas_fuentes()
    assert resultado["modo"] == "RECETA_COMPLETA"
    assert antes == despues
    assert resultado["datos_modificados"] is False


def test_i1321_encadena_detector_i131(tmp_path):
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True)
    (db / "escandallos_canonicos.json").write_text(json.dumps({"escandallos": RECETAS}), encoding="utf-8")
    (db / "articulos.json").write_text(json.dumps({"articulos": ARTICULOS}), encoding="utf-8")
    excel = tmp_path / "menu.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "MENU TEST"
    ws.append(["MENU TEST"])
    ws.append(["APERITIVO"])
    ws.append(["PLATO", "GR O KG", "PRECIO KG", "EUROS/RACION"])
    ws.append(["Ceviche de corvina", 1, 2, 2])
    ws.append(["Tataki de atún con sésamo", 1, 3, 3])
    wb.save(excel)
    resultado = MotorReconocimientoMenusI1321(tmp_path).preparar_desde_excel(excel, ["MENU TEST"])
    assert resultado["resumen"]["platos"] == 2
    assert resultado["resumen"]["recetas_completas"] == 2
    assert resultado["datos_modificados"] is False


def test_i13211_carga_recetas_operativas_y_prioriza_sobre_articulos(tmp_path):
    db = tmp_path / "DATOS" / "db"
    db.mkdir(parents=True)
    (db / "escandallos.json").write_text(json.dumps([
        {"receta_id": "ROP1", "nombre": "Taco de carrillera"},
        {"receta_id": "ROP2", "nombre": "Sorbete mandarina"},
    ]), encoding="utf-8")
    (db / "escandallos_canonicos.json").write_text(json.dumps({"escandallos": [
        {"receta": {"codigo": "RC1", "nombre": "Ceviche de corvina"}}
    ]}), encoding="utf-8")
    (db / "articulos.json").write_text(json.dumps([
        {"codigo": "A1", "nombre": "Taco de Carrillera porc"},
        {"codigo": "A2", "nombre": "Sorbete mandarina boda"},
    ]), encoding="utf-8")
    motor = MotorReconocimientoMenusI1321(tmp_path)
    taco = motor.reconocer_texto("Taco de Carrillera porc")
    sorbete = motor.reconocer_texto("Sorbete mandarina boda")
    assert len(motor.recetas) == 3
    assert taco["modo"] == "RECETA_COMPLETA"
    assert taco["coincidencias"][0]["tipo"] == "RECETA"
    assert taco["coincidencias"][0]["estado"] == "EQUIVALENTE_COMPLETA"
    assert sorbete["modo"] == "RECETA_COMPLETA"


def test_i13211_no_convierte_plato_compuesto_en_receta_completa(tmp_path):
    motor = MotorReconocimientoMenusI1321(tmp_path, [
        {"codigo": "R1", "nombre": "Solomillo de cerdo"},
        {"codigo": "R2", "nombre": "Salsa naranja"},
    ], [])
    resultado = motor.reconocer_texto("Solomillo de cerdo con parmentier patata i salsa naranja")
    assert resultado["modo"] == "MAPA_PARCIAL"
    assert [x["nombre"] for x in resultado["coincidencias"]] == ["Solomillo de cerdo", "Salsa naranja"]


def test_i13211_articulo_completo_tiene_modo_coherente(tmp_path):
    motor = MotorReconocimientoMenusI1321(tmp_path, [], [{"codigo": "A1", "nombre": "Pan especial"}])
    resultado = motor.reconocer_texto("Pan especial")
    assert resultado["modo"] == "ARTICULO_COMPLETO"
