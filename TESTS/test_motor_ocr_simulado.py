from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def crear_png_minimo(path: Path):
    path.write_bytes(bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
        "0000000A49444154789C63600000020001E221BC330000000049454E44AE426082"
    ))

def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    img = BASE_DIR / "DATOS" / "facturas" / "factura_escaneada_demo.png"
    img.parent.mkdir(parents=True, exist_ok=True)
    crear_png_minimo(img)

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "motor_ocr_simulado" for p in listado.datos["pipelines"])

    texto = "MAKRO ESPAÑA S.A.\\nFactura Nº F-OCR-1\\nCarrillera Ternera 8 KG 8,45 67,60\\nTotal factura 67,60"
    reg = core.orquestador.resolver(SolicitudHostAI("registrar_texto_ocr_manual", {
        "ruta_archivo": str(img),
        "texto": texto,
    }))
    assert reg.ok is True

    ocr = core.orquestador.resolver(SolicitudHostAI("extraer_texto_ocr", {
        "ruta_archivo": str(img)
    }))
    assert ocr.ok is True
    assert "Carrillera" in ocr.datos["texto_extraido"]
    assert ocr.datos["metodo"] == "manual_cache"

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_resultado_ocr", {
        "resultado": ocr.datos,
        "nombre": "test_resultado_ocr.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.7.2 Motor OCR Simulado")
    print("OCR:", ocr.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
