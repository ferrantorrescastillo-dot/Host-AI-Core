from pathlib import Path
import sys

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
    ws.append(["Codigo", "Articulo", "Unidad", "Familia", "Proveedor", "Precio", "Stock Minimo", "Ubicacion", "Alergenos"])
    ws.append(["ART-CARRILLERA", "Carrillera de ternera", "kg", "carnes", "Proveedor Carnes", 8.5, 3, "Camara 1", ""])
    ws.append(["ART-CEBOLLA", "Cebolla", "kg", "verduras", "Proveedor Verduras", 1.2, 5, "Almacen seco", ""])
    ws.append(["ART-DEMI", "Demi-glace", "L", "salsas", "Producción interna", 3.0, 2, "Camara 2", ""])
    wb.save(path)

def ejecutar_prueba():
    demo_path = BASE_DIR / "DATOS" / "importaciones" / "excel_demo_importador_articulos.xlsx"
    demo_path.parent.mkdir(parents=True, exist_ok=True)
    crear_excel_demo(demo_path)

    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "importador_articulos_excel" for p in listado.datos["pipelines"])

    preview = core.orquestador.resolver(SolicitudHostAI("vista_previa_articulos_excel", {
        "ruta_archivo": str(demo_path),
        "filas_preview": 50,
    }))
    assert preview.ok is True
    assert preview.datos["articulos_detectados"] == 3
    assert preview.datos["articulos_importados"] == 0
    assert len(preview.datos["articulos"]) == 3

    imp = core.orquestador.resolver(SolicitudHostAI("importar_articulos_excel", {
        "ruta_archivo": str(demo_path),
        "filas_preview": 50,
        "actualizar_existentes": True,
    }))
    assert imp.ok is True
    assert imp.datos["articulos_importados"] == 3
    assert imp.datos["precios_registrados"] == 3
    assert "ART-CARRILLERA" in core.importador_articulos_excel.articulos
    assert "ART-CEBOLLA" in core.importador_articulos_excel.articulos

    lista = core.orquestador.resolver(SolicitudHostAI("listar_articulos_importados_excel", {}))
    assert lista.ok is True
    assert lista.datos["total"] == 3

    precios = core.orquestador.resolver(SolicitudHostAI("listar_precios", {}))
    assert precios.ok is True
    assert precios.datos["total"] >= 3

    print("TEST OK - Host AI 3.0.2.5 Importador Artículos Excel")
    print("Preview:", preview.to_dict())
    print("Importación:", imp.to_dict())
    print("Artículos:", lista.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
