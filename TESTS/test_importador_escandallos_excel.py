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
    ws.title = "Escandallos"
    ws.append(["Receta", "Ingrediente", "Cantidad", "Unidad", "Merma", "Precio", "Familia", "Proveedor"])
    ws.append(["Carrillera melosa", "Carrillera de ternera", 1.8, "kg", 10, 8.5, "carnes", "Proveedor Carnes"])
    ws.append(["Carrillera melosa", "Demi-glace", 0.8, "L", 0, 3.0, "salsas", "Producción interna"])
    ws.append(["Bacalao pilpil", "Bacalao", 1.5, "kg", 5, 12.0, "pescados", "Proveedor Pescado"])
    ws.append(["Bacalao pilpil", "Aceite oliva", 0.5, "L", 0, 5.0, "aceites", "Proveedor Aceite"])
    wb.save(path)

def ejecutar_prueba():
    demo_path = BASE_DIR / "DATOS" / "importaciones" / "excel_demo_importador_escandallos.xlsx"
    demo_path.parent.mkdir(parents=True, exist_ok=True)
    crear_excel_demo(demo_path)

    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "importador_escandallos_excel" for p in listado.datos["pipelines"])

    preview = core.orquestador.resolver(SolicitudHostAI("vista_previa_escandallos_excel", {
        "ruta_archivo": str(demo_path),
        "filas_preview": 50,
    }))
    assert preview.ok is True
    assert preview.datos["recetas_detectadas"] == 2
    assert preview.datos["lineas_importadas"] == 4
    assert preview.datos["escandallos_importados"] == 0
    assert len(preview.datos["escandallos"]) == 2

    imp = core.orquestador.resolver(SolicitudHostAI("importar_escandallos_excel", {
        "ruta_archivo": str(demo_path),
        "filas_preview": 50,
        "reemplazar": True,
    }))
    assert imp.ok is True
    assert imp.datos["escandallos_importados"] == 2
    assert "REC-CARRILLERA-MELOSA" in core.escandallos_inteligente.escandallos
    assert "REC-BACALAO-PILPIL" in core.escandallos_inteligente.escandallos

    calc = core.orquestador.resolver(SolicitudHostAI("calcular_escandallo_receta", {
        "receta_id": "REC-CARRILLERA-MELOSA",
        "raciones": 10,
    }))
    assert calc.ok is True
    assert len(calc.datos["necesidades"]) == 2
    carrillera = [n for n in calc.datos["necesidades"] if n["nombre"] == "Carrillera de ternera"][0]
    assert round(carrillera["cantidad_bruta"], 2) == 1.98

    resumen_db = core.orquestador.resolver(SolicitudHostAI("resumen_db", {}))
    assert resumen_db.ok is True

    print("TEST OK - Host AI 3.0.2.4 Importador Escandallos Excel")
    print("Preview:", preview.to_dict())
    print("Importación:", imp.to_dict())
    print("Cálculo:", calc.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
