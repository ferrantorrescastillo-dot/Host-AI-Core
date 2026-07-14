from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "validador_corrector_ocr" for p in listado.datos["pipelines"])

    texto = "MAKRO ESPAÑA S.A.\\nF actura N0 F-1\\nCarrillera Ternera 8 KG 8.45 67.60\\nT0TAL 67.60"
    val = core.orquestador.resolver(SolicitudHostAI("validar_texto_ocr", {"texto": texto}))
    assert val.ok is True
    assert "Factura" in val.datos["texto_corregido"]
    assert "8,45" in val.datos["texto_corregido"]
    assert len(val.datos["correcciones"]) >= 2

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_validacion_ocr", {
        "validacion": val.datos,
        "nombre": "test_validacion_ocr.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.7.4 Validador Corrector OCR")
    print("Validación:", val.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
