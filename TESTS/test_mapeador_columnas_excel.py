from pathlib import Path
import sys
from datetime import date

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from openpyxl import Workbook
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def crear_excel_demo(path: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Escandallos"
    ws.append(["Plato", "Materia Prima", "Cant", "Uds", "P.Unit", "% Merma", "Obs Internas"])
    ws.append(["Carrillera melosa", "Carrillera de ternera", 1.8, "kg", 8.5, 10, "limpiar bien"])
    ws.append(["Carrillera melosa", "Demi-glace", 0.8, "L", 3.0, 0, ""])

    ws2 = wb.create_sheet("Inventario")
    ws2.append(["Producto", "Existencias", "Ud", "Cámara", "Fecha Caducidad"])
    ws2.append(["Carrillera", 10, "kg", "Cámara 1", date(2026, 7, 20)])
    wb.save(path)

def ejecutar_prueba():
    demo_path = BASE_DIR / "DATOS" / "importaciones" / "excel_demo_mapeador.xlsx"
    demo_path.parent.mkdir(parents=True, exist_ok=True)
    crear_excel_demo(demo_path)

    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "mapeador_columnas_excel" for p in listado.datos["pipelines"])

    mapeo = core.orquestador.resolver(SolicitudHostAI("mapear_columnas_excel", {
        "ruta_archivo": str(demo_path),
        "filas_preview": 5,
    }))
    assert mapeo.ok is True
    hojas = {h["hoja"]: h for h in mapeo.datos["hojas"]}
    esc = hojas["Escandallos"]
    campos = {m["columna_original"]: m["campo_canonico"] for m in esc["mapeos"]}

    assert campos["Plato"] == "RECETA"
    assert campos["Materia Prima"] == "INGREDIENTE"
    assert campos["Cant"] == "CANTIDAD"
    assert campos["Uds"] == "UNIDAD"
    assert campos["P.Unit"] == "PRECIO"
    assert campos["% Merma"] == "MERMA"
    assert "Obs Internas" in campos

    inv = hojas["Inventario"]
    campos_inv = {m["columna_original"]: m["campo_canonico"] for m in inv["mapeos"]}
    assert campos_inv["Producto"] == "ARTICULO"
    assert campos_inv["Existencias"] == "CANTIDAD"
    assert campos_inv["Ud"] == "UNIDAD"
    assert campos_inv["Cámara"] == "UBICACION"
    assert campos_inv["Fecha Caducidad"] == "CADUCIDAD"

    aprender = core.orquestador.resolver(SolicitudHostAI("aprender_columna_excel", {
        "columna_original": "Referencia proveedor",
        "campo_canonico": "ARTICULO",
    }))
    assert aprender.ok is True

    dic = core.orquestador.resolver(SolicitudHostAI("listar_diccionario_columnas_excel", {}))
    assert dic.ok is True
    assert "referencia proveedor" in dic.datos["aprendidos"]
    assert dic.datos["aprendidos"]["referencia proveedor"] == "ARTICULO"

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_diccionario_columnas_excel", {}))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.2.3 Mapeador Inteligente de Columnas")
    print("Mapeo:", mapeo.to_dict())
    print("Diccionario:", dic.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
