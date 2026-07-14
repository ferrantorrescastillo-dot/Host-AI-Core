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
    ws.title = "Inventario"
    ws.append(["Codigo", "Producto", "Cantidad", "Unidad", "Ubicacion", "Caducidad", "Lote", "Proveedor", "Precio", "Familia"])
    ws.append(["ART-CARRILLERA", "Carrillera de ternera", 10, "kg", "Camara 1", date(2026, 7, 20), "L001", "Proveedor Carnes", 8.5, "carnes"])
    ws.append(["ART-CEBOLLA", "Cebolla", 5, "kg", "Almacen seco", date(2026, 7, 25), "L002", "Proveedor Verduras", 1.2, "verduras"])
    ws.append(["ART-DEMI", "Demi-glace", 2, "L", "Camara 2", date(2026, 7, 18), "L003", "Producción interna", 3.0, "salsas"])
    wb.save(path)

def ejecutar_prueba():
    demo_path = BASE_DIR / "DATOS" / "importaciones" / "excel_demo_importador_inventario.xlsx"
    demo_path.parent.mkdir(parents=True, exist_ok=True)
    crear_excel_demo(demo_path)

    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "importador_inventario_excel" for p in listado.datos["pipelines"])

    preview = core.orquestador.resolver(SolicitudHostAI("vista_previa_inventario_excel", {
        "ruta_archivo": str(demo_path),
        "filas_preview": 50,
    }))
    assert preview.ok is True
    assert preview.datos["lineas_detectadas"] == 3
    assert preview.datos["lineas_importadas"] == 0
    assert len(preview.datos["cambios"]) == 3

    imp = core.orquestador.resolver(SolicitudHostAI("importar_inventario_excel", {
        "ruta_archivo": str(demo_path),
        "filas_preview": 50,
        "crear_articulos": True,
        "actualizar_stock": True,
    }))
    assert imp.ok is True
    assert imp.datos["lineas_importadas"] == 3
    assert imp.datos["articulos_creados"] == 3
    assert imp.datos["stock_actualizado"] >= 3

    stock = core.orquestador.resolver(SolicitudHostAI("stock_actual", {}))
    assert stock.ok is True
    items = {i["articulo_id"]: i for i in stock.datos.get("items", [])}
    assert "ART-CARRILLERA" in items
    assert round(items["ART-CARRILLERA"]["cantidad"], 2) == 10
    assert "ART-CEBOLLA" in items
    assert round(items["ART-CEBOLLA"]["cantidad"], 2) == 5

    precios = core.orquestador.resolver(SolicitudHostAI("listar_precios", {}))
    assert precios.ok is True
    assert precios.datos["total"] >= 3

    comparar = core.orquestador.resolver(SolicitudHostAI("comparar_inventario_excel", {
        "ruta_archivo": str(demo_path),
        "filas_preview": 50,
    }))
    assert comparar.ok is True
    assert comparar.datos["total_cambios"] == 3

    print("TEST OK - Host AI 3.0.2.6 Importador Inventario Excel")
    print("Preview:", preview.to_dict())
    print("Importación:", imp.to_dict())
    print("Stock:", stock.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
