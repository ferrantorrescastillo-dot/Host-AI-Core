from pathlib import Path

from openpyxl import Workbook

from SERVICIOS.importador_menus_legacy_i13 import ImportadorMenusLegacyI13


class DBMemoria:
    def __init__(self):
        self.datos = {"menus": []}

    def cargar(self, coleccion):
        return list(self.datos.get(coleccion, []))

    def guardar(self, coleccion, datos):
        self.datos[coleccion] = list(datos)


def _excel_menu(ruta: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = "MENU BODA 31-1"
    ws.append(["MENÚ BODA 31-1"])
    ws.append(["Cóctel"])
    ws.append(["Ceviche de corvina", 0.60])
    ws.append(["Taco de carrillera", 1.80])
    ws.append(["Entrante"])
    ws.append(["Crema caliente de tomate", 2.10])
    ws.append(["Segundo"])
    ws.append(["Solomillo de cerdo con parmentier", 5.20])
    ws.append(["Postre"])
    ws.append(["Sorbete de mandarina", 1.20])
    ws.append(["Precio venta", 45.0])
    ws.append(["Coste total", 10.90])
    ws.append(["Food cost", 24.22])
    wb.save(ruta)


def _recetas():
    nombres = [
        "Ceviche de corvina",
        "Taco de carrillera",
        "Crema caliente de tomate",
        "Solomillo de cerdo con parmentier",
        "Sorbete de mandarina",
    ]
    return [{"receta_id": f"REC-{i}", "nombre": n} for i, n in enumerate(nombres, 1)]


def test_i13_detecta_menu_y_vincula_recetas(tmp_path):
    ruta = tmp_path / "menus.xlsx"
    _excel_menu(ruta)
    servicio = ImportadorMenusLegacyI13()
    previa = servicio.preparar(ruta, recetas_existentes=_recetas())
    assert previa["resumen"]["menus_detectados"] == 1
    assert previa["resumen"]["platos"] == 5
    assert previa["resumen"]["vinculos_exactos"] == 5
    menu = previa["menus"][0]
    assert menu["precio_venta"] == 45.0
    assert menu["coste_total_declarado"] == 10.9
    assert menu["food_cost_pct"] == 24.22
    assert {p["seccion"] for p in menu["platos"]} >= {"Cóctel", "Entrante", "Segundo", "Postre"}


def test_i13_importacion_segura_y_control_duplicados(tmp_path):
    ruta = tmp_path / "menus.xlsx"
    _excel_menu(ruta)
    servicio = ImportadorMenusLegacyI13()
    previa = servicio.preparar(ruta, recetas_existentes=_recetas())
    db = DBMemoria()
    resultado = servicio.importar(previa, db, confirmar=True)
    assert resultado["resumen"]["importados"] == 1
    guardado = db.cargar("menus")[0]
    assert guardado["nombre"] == "MENÚ BODA 31-1"
    assert guardado["secciones"]["Cóctel"][0]["receta_id"]

    previa_duplicada = servicio.preparar(
        ruta,
        recetas_existentes=_recetas(),
        menus_existentes=db.cargar("menus"),
    )
    resultado_duplicado = servicio.importar(previa_duplicada, db, confirmar=True)
    assert resultado_duplicado["resumen"]["importados"] == 0
    assert resultado_duplicado["resumen"]["omitidos"] == 1
