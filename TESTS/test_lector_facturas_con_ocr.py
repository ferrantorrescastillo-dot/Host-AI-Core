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
    )

    img = BASE_DIR / "DATOS" / "facturas" / "factura_ocr_integrada.png"
    img.parent.mkdir(parents=True, exist_ok=True)
    crear_png_minimo(img)

    texto = """MAKRO ESPAÑA S.A.
Factura Nº F-OCR-2
Carrillera Ternera 8 KG 8,45 67,60
Total factura 67,60"""

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "lector_facturas_con_ocr" for p in listado.datos["pipelines"])

    lectura = core.orquestador.resolver(SolicitudHostAI("leer_factura_archivo_con_ocr", {
        "ruta_archivo": str(img),
        "texto_manual": texto,
    }))
    assert lectura.ok is True
    assert lectura.datos["ok"] is True
    assert lectura.datos["origen"] == "ocr"
    assert lectura.datos["total_lineas"] == 1

    completo = core.orquestador.resolver(SolicitudHostAI("validar_y_relacionar_factura_ocr", {
        "ruta_archivo": str(img),
        "texto_manual": texto,
    }))
    assert completo.ok is True
    assert completo.datos["ok"] is True
    assert completo.datos["lectura"]["total_lineas"] == 1

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_lectura_factura_ocr", {
        "lectura": lectura.datos,
        "nombre": "test_lectura_factura_ocr.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.7.3 Integración OCR Facturas")
    print("Lectura:", lectura.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
