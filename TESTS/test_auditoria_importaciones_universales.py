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

    img = BASE_DIR / "DATOS" / "facturas" / "factura_auditoria_universal.png"
    img.parent.mkdir(parents=True, exist_ok=True)
    crear_png_minimo(img)

    texto = """MAKRO ESPAÑA S.A.
Factura Nº F-AUD-1
Carrillera Ternera 8 KG 8,45 67,60
Total factura 67,60"""

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "auditoria_importaciones_universales" for p in listado.datos["pipelines"])

    ejecutado = core.orquestador.resolver(SolicitudHostAI("ejecutar_importacion_factura_archivo", {
        "ruta_archivo": str(img),
        "texto_manual_ocr": texto,
        "forzar": True,
    }))
    assert ejecutado.ok is True
    assert ejecutado.datos["aplicado"] is True
    assert "auditoria" in ejecutado.datos

    lista = core.orquestador.resolver(SolicitudHostAI("listar_auditoria_importaciones", {}))
    assert lista.ok is True
    assert lista.datos["total"] >= 1

    resumen = core.orquestador.resolver(SolicitudHostAI("resumen_auditoria_importaciones", {}))
    assert resumen.ok is True
    assert resumen.datos["aplicadas"] >= 1

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_auditoria_importaciones", {}))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.8.3 Auditoría Importaciones Universales")
    print("Resumen:", resumen.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
