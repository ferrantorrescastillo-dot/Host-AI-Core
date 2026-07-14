from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI
from MODELOS.importacion_articulos_excel import ArticuloImportadoExcel

def crear_png_minimo(path: Path):
    path.write_bytes(bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
        "0000000A49444154789C63600000020001E221BC330000000049454E44AE426082"
    ))

def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    core.importador_articulos_excel.articulos["ART-CARRILLERA"] = ArticuloImportadoExcel(
        nombre="Carrillera de ternera",
        articulo_id="ART-CARRILLERA",
        unidad="kg",
        familia="carnes",
        precio_unitario=8.0,
    )

    img = BASE_DIR / "DATOS" / "facturas" / "factura_ejecutor_universal.png"
    img.parent.mkdir(parents=True, exist_ok=True)
    crear_png_minimo(img)

    texto = """MAKRO ESPAÑA S.A.
Factura Nº F-EJEC-1
Carrillera Ternera 8 KG 8,45 67,60
Total factura 67,60"""

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "ejecutor_importador_universal_facturas" for p in listado.datos["pipelines"])

    no_forzado = core.orquestador.resolver(SolicitudHostAI("ejecutar_importacion_factura_archivo", {
        "ruta_archivo": str(img),
        "texto_manual_ocr": texto,
        "forzar": False,
    }))
    assert no_forzado.ok is True
    assert no_forzado.datos["aplicado"] is False

    ejecutado = core.orquestador.resolver(SolicitudHostAI("ejecutar_importacion_factura_archivo", {
        "ruta_archivo": str(img),
        "texto_manual_ocr": texto,
        "forzar": True,
    }))
    assert ejecutado.ok is True
    assert ejecutado.datos["aplicado"] is True
    assert ejecutado.datos["aplicacion_stock"]["aplicados"] >= 1

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_resultado_importacion_factura", {
        "resultado": ejecutado.datos,
        "nombre": "test_resultado_importacion_factura.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.8.2 Ejecutor Importador Universal Facturas")
    print("Ejecución:", ejecutado.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
