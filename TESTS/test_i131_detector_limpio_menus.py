from pathlib import Path

from openpyxl import Workbook

from SERVICIOS.detector_limpio_menus_i131 import DetectorLimpioMenusI131


def _crear_excel_realista(ruta: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = "MENU BODA 31-1"
    ws.append([None])
    ws.append(["MENU BODA "])
    ws.append([None])
    ws.append(["APERITIVO.", "P.V.P", "NETO ", "COSTO", "FOOD COST"])
    ws.append(["COCTEL BIENVENIDA EN LA PLAZA 1 HORA", "GR O KG.", "PRECIO KG", "EUROS/RACION."])
    platos = [
        ("Ceviche de corvina", 1, 0.5946172414, 0.5946172414),
        ("Taco de Carrillera porc", 1, 1.4557586207, 1.4557586207),
        ("Guacamole y totopos", 1, 0.8370689655, 0.8370689655),
        ("Brocheta langostino", 1, 0.7561379310, 0.7561379310),
        ("Pan de cristal con jamón", 1, 1.6585, 1.6585),
        ("Tabla de quesos", 1, 0.1574827586, 0.1574827586),
        ("Agua de jamaica", 1, 0.1517241379, 0.1517241379),
        ("Agua de limón", 1, 0.1062068966, 0.1062068966),
    ]
    for p in platos:
        ws.append(list(p))
    ws.append(["Entrante"])
    ws.append(["Crema calenta tomàquet", 1, 0.8870258621, 0.8870258621])
    ws.append(["PRIMERO."])
    ws.append(["Flor de alcachofa con jamón", 1, 0.3939655172, 0.3939655172])
    ws.append(["SEGUNDO"])
    ws.append(["Solomillo de cerdo con parmentier patata i salsa naranja", 1, 1.4276724138, 1.4276724138])
    ws.append(["POSTRE"])
    ws.append(["Sorbete mandarina boda", 1, 0.2493103448, 0.2493103448])
    ws.append(["BODEGA, PAN, VINO Y CAFES."])
    ws.append(["Pan individual rombo makro", 0.05, 3.85, 0.1925])
    for _ in range(5):
        ws.append([None])
    ws.append(["ESCANDALLO", 75, 67.5, 8.8679706897, 0.1182396092])
    ws.append([None])
    ws.append([None, None, None, 66.1320293103, "Benefici"])
    wb.save(ruta)


def test_i131_clasifica_limpio_y_lee_costes(tmp_path):
    ruta = tmp_path / "Escandallos Boronat.xlsx"
    _crear_excel_realista(ruta)
    previa = DetectorLimpioMenusI131().preparar(ruta, hojas=["MENU BODA 31-1"])
    assert previa["modo"] == "vista_previa_sin_escritura_sin_vinculacion"
    assert previa["resumen"]["menus_detectados"] == 1
    assert previa["resumen"]["platos"] == 12
    assert previa["resumen"]["articulos_directos"] == 1
    assert previa["resumen"]["complementos"] == 1
    menu = previa["menus"][0]
    assert menu["platos"][0]["coste_racion"] == 0.5946172414
    assert menu["platos"][0]["coste_racion"] != menu["platos"][0]["cantidad"]
    assert menu["articulos_directos"][0]["nombre"] == "Pan individual rombo makro"
    tipos_por_texto = {f["texto"]: f["tipo"] for f in menu["filas"] if f["texto"]}
    assert tipos_por_texto["COCTEL BIENVENIDA EN LA PLAZA 1 HORA"] == "SECCION"
    assert tipos_por_texto["BODEGA, PAN, VINO Y CAFES."] == "COMPLEMENTO"
    assert tipos_por_texto["ESCANDALLO"] == "RESUMEN_ECONOMICO"
    assert tipos_por_texto["Benefici"] == "RESUMEN_ECONOMICO"


def test_i131_extrae_economia_real(tmp_path):
    ruta = tmp_path / "Escandallos Boronat.xlsx"
    _crear_excel_realista(ruta)
    menu = DetectorLimpioMenusI131().preparar(ruta, hojas=["MENU BODA 31-1"])["menus"][0]
    eco = menu["economico"]
    assert eco["precio_venta"] == 75.0
    assert eco["venta_neta"] == 67.5
    assert round(eco["coste_total"], 6) == round(8.8679706897, 6)
    assert round(eco["food_cost_pct"], 5) == round(11.82396092, 5)
    assert round(eco["beneficio"], 6) == round(66.1320293103, 6)


def test_i131_no_tiene_metodo_importar():
    detector = DetectorLimpioMenusI131()
    assert not hasattr(detector, "importar")
