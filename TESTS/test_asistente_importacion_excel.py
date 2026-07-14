from pathlib import Path
import sys
from datetime import date

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from openpyxl import Workbook
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def crear_excel_articulos(path: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Listado Articulos"
    ws.append(["Codigo", "Articulo", "Unidad", "Familia", "Proveedor", "Precio"])
    ws.append(["ART-CARRILLERA", "Carrillera de ternera", "kg", "carnes", "Proveedor Carnes", 8.5])
    ws.append(["ART-CEBOLLA", "Cebolla", "kg", "verduras", "Proveedor Verduras", 1.2])
    wb.save(path)

def crear_excel_inventario(path: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Inventario"
    ws.append(["Codigo", "Producto", "Cantidad", "Unidad", "Ubicacion", "Caducidad", "Proveedor", "Precio", "Familia"])
    ws.append(["ART-CARRILLERA", "Carrillera de ternera", 10, "kg", "Camara 1", date(2026, 7, 20), "Proveedor Carnes", 8.5, "carnes"])
    ws.append(["ART-CEBOLLA", "Cebolla", 5, "kg", "Almacen seco", date(2026, 7, 25), "Proveedor Verduras", 1.2, "verduras"])
    wb.save(path)

def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "asistente_importacion_excel" for p in listado.datos["pipelines"])

    art_path = BASE_DIR / "DATOS" / "importaciones" / "excel_demo_asistente_articulos.xlsx"
    inv_path = BASE_DIR / "DATOS" / "importaciones" / "excel_demo_asistente_inventario.xlsx"
    art_path.parent.mkdir(parents=True, exist_ok=True)
    crear_excel_articulos(art_path)
    crear_excel_inventario(inv_path)

    prep_art = core.orquestador.resolver(SolicitudHostAI("preparar_importacion_excel", {
        "ruta_archivo": str(art_path),
        "filas_preview": 50,
    }))
    assert prep_art.ok is True
    assert prep_art.datos["estado"] == "lista_para_importar"
    assert "articulos" in prep_art.datos["importadores_sugeridos"]
    sesion_art = prep_art.datos["id"]

    exec_art = core.orquestador.resolver(SolicitudHostAI("ejecutar_importacion_excel", {
        "sesion_id": sesion_art,
        "importador": "auto",
        "filas_preview": 50,
    }))
    assert exec_art.ok is True
    assert exec_art.datos["estado"] == "importada"
    assert exec_art.datos["resultado_importacion"]["articulos_importados"] == 2

    prep_inv = core.orquestador.resolver(SolicitudHostAI("preparar_importacion_excel", {
        "ruta_archivo": str(inv_path),
        "filas_preview": 50,
    }))
    assert prep_inv.ok is True
    assert "inventario" in prep_inv.datos["importadores_sugeridos"]
    sesion_inv = prep_inv.datos["id"]

    exec_inv = core.orquestador.resolver(SolicitudHostAI("ejecutar_importacion_excel", {
        "sesion_id": sesion_inv,
        "importador": "inventario",
        "filas_preview": 50,
    }))
    assert exec_inv.ok is True
    assert exec_inv.datos["estado"] == "importada"
    assert exec_inv.datos["resultado_importacion"]["lineas_importadas"] == 2

    sesiones = core.orquestador.resolver(SolicitudHostAI("listar_sesiones_importacion_excel", {}))
    assert sesiones.ok is True
    assert sesiones.datos["total"] == 2

    stock = core.orquestador.resolver(SolicitudHostAI("stock_actual", {}))
    assert stock.ok is True
    assert stock.datos["total_items"] >= 2

    print("TEST OK - Host AI 3.0.2.8 Asistente Importación Excel")
    print("Preparar artículos:", prep_art.to_dict())
    print("Ejecutar inventario:", exec_inv.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
