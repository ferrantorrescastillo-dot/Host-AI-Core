from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def crear_png_minimo(path: Path):
    # PNG 1x1 transparente mínimo
    path.write_bytes(bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
        "0000000A49444154789C63600000020001E221BC330000000049454E44AE426082"
    ))

def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    img = BASE_DIR / "DATOS" / "facturas" / "test_ocr_imagen.png"
    img.parent.mkdir(parents=True, exist_ok=True)
    crear_png_minimo(img)

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "base_ocr_documentos" for p in listado.datos["pipelines"])

    diag = core.orquestador.resolver(SolicitudHostAI("diagnosticar_ocr_archivo", {
        "ruta_archivo": str(img)
    }))
    assert diag.ok is True
    assert diag.datos["necesita_ocr"] is True
    assert diag.datos["paginas"] == 1

    lote = core.orquestador.resolver(SolicitudHostAI("diagnosticar_ocr_lote", {
        "rutas": [str(img)]
    }))
    assert lote.ok is True
    assert lote.datos["necesitan_ocr"] == 1

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_diagnostico_ocr", {
        "diagnostico": diag.datos,
        "nombre": "test_diagnostico_ocr.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.7.1 Base OCR Documentos")
    print("Diagnóstico:", diag.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
