from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from openpyxl import Workbook
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def crear_excel_conflictos(path: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Listado Articulos"
    ws.append(["Codigo", "Articulo", "Unidad", "Familia", "Proveedor", "Precio"])
    ws.append(["ART-CARRILLERA", "Carrillera de ternera", "kg", "carnes", "Proveedor Carnes", 12.0])
    ws.append(["ART-CARRILLERA", "Carrillera ternera", "kg", "carnes", "Proveedor Carnes", 12.0])
    wb.save(path)

def ejecutar_prueba():
    demo_path = BASE_DIR / "DATOS" / "importaciones" / "excel_demo_conflictos.xlsx"
    demo_path.parent.mkdir(parents=True, exist_ok=True)
    crear_excel_conflictos(demo_path)

    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    # Creamos un precio/artículo previo más bajo para provocar cambio fuerte.
    from MODELOS.importacion_articulos_excel import ArticuloImportadoExcel
    core.importador_articulos_excel.articulos["ART-CARRILLERA"] = ArticuloImportadoExcel(
        nombre="Carrillera de ternera",
        articulo_id="ART-CARRILLERA",
        unidad="kg",
        familia="carnes",
        proveedor="Proveedor Carnes",
        precio_unitario=8.0,
    )
    core.costes_inteligente.registrar_precio(
        nombre="Carrillera de ternera",
        precio_unitario=8.0,
        unidad="kg",
        articulo_id="ART-CARRILLERA",
        proveedor="Proveedor Carnes",
        familia="carnes",
    )

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "conflictos_excel" for p in listado.datos["pipelines"])

    informe = core.orquestador.resolver(SolicitudHostAI("analizar_conflictos_excel", {
        "ruta_archivo": str(demo_path),
        "filas_preview": 50,
    }))
    assert informe.ok is True
    assert informe.datos["total_conflictos"] >= 2

    tipos = {c["tipo"] for c in informe.datos["conflictos"]}
    assert "duplicado_excel" in tipos
    assert "cambio_precio_fuerte" in tipos

    resumen = core.orquestador.resolver(SolicitudHostAI("resumen_conflictos_excel", {}))
    assert resumen.ok is True
    assert resumen.datos["total_conflictos"] == informe.datos["total_conflictos"]

    primer_id = informe.datos["conflictos"][0]["id"]
    resolver = core.orquestador.resolver(SolicitudHostAI("resolver_conflicto_excel", {
        "conflicto_id": primer_id,
        "decision": "revisar",
    }))
    assert resolver.ok is True

    print("TEST OK - Host AI 3.0.2.7 Resolución Conflictos Excel")
    print("Informe:", informe.to_dict())
    print("Resolución:", resolver.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
