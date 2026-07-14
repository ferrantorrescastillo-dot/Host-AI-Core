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
    ws.title = "Listado Articulos"
    ws.append(["Articulo", "Cantidad", "Unidad", "Precio", "Fecha", "Columna Vacia"])
    ws.append(["Carrillera de ternera", 10, "kg", 8.5, date(2026, 7, 8), None])
    ws.append(["Cebolla", 5, "kg", 1.2, date(2026, 7, 8), None])
    ws.append(["Demi-glace", 2, "L", 3.0, date(2026, 7, 8), None])

    ws2 = wb.create_sheet("Escandallos")
    ws2.append(["Receta", "Ingrediente", "Cantidad", "Unidad", "Merma"])
    ws2.append(["Carrillera melosa", "Carrillera de ternera", 1.8, "kg", 10])
    ws2.append(["Carrillera melosa", "Demi-glace", 0.8, "L", 0])

    wb.save(path)


def ejecutar_prueba():
    demo_path = BASE_DIR / "DATOS" / "importaciones" / "excel_demo_lector.xlsx"
    demo_path.parent.mkdir(parents=True, exist_ok=True)
    crear_excel_demo(demo_path)

    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "excel" for p in listado.datos["pipelines"])

    analisis = core.orquestador.resolver(SolicitudHostAI("analizar_excel", {
        "ruta_archivo": str(demo_path),
        "filas_preview": 5,
        "exportar_json": True,
    }))
    assert analisis.ok is True
    assert analisis.datos["total_hojas"] == 2
    assert analisis.datos["total_filas"] >= 5
    assert "json_exportado" in analisis.datos

    hojas = {h["nombre"]: h for h in analisis.datos["hojas"]}
    assert "Listado Articulos" in hojas
    assert "Escandallos" in hojas

    listado_articulos = hojas["Listado Articulos"]
    columnas = {c["nombre_detectado"]: c for c in listado_articulos["columnas_detectadas"]}

    assert columnas["Articulo"]["tipo_detectado"] == "texto"
    assert columnas["Cantidad"]["tipo_detectado"] == "numero"
    assert columnas["Precio"]["tipo_detectado"] == "numero"
    assert columnas["Fecha"]["tipo_detectado"] == "fecha"
    assert columnas["Columna Vacia"]["tipo_detectado"] == "vacio"
    assert columnas["Columna Vacia"]["porcentaje_vacio"] == 100.0

    assert len(listado_articulos["vista_previa"]) == 3
    assert listado_articulos["vista_previa"][0]["Articulo"] == "Carrillera de ternera"

    json_path = Path(analisis.datos["json_exportado"])
    assert json_path.exists()

    print("TEST OK - Host AI 3.0.2.1 Lector Universal Excel")
    print("Análisis:", analisis.to_dict())


if __name__ == "__main__":
    ejecutar_prueba()
