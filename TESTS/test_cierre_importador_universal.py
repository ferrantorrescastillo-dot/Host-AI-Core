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
    assert any(p["nombre"] == "cierre_importador_universal" for p in listado.datos["pipelines"])

    cierre = core.orquestador.resolver(SolicitudHostAI("comprobar_cierre_importador_universal", {}))
    assert cierre.ok is True
    assert cierre.datos["listo_para_uso"] is True
    assert len(cierre.datos["modulos_faltantes"]) == 0
    assert "aplicar_stock" in cierre.datos["flujo_completo"]

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_cierre_importador_universal", {
        "informe": cierre.datos,
        "nombre": "test_cierre_importador_universal.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.8.5 Cierre Importador Universal")
    print("Cierre OK:", cierre.datos["listo_para_uso"], len(cierre.datos["modulos_comprobados"]))

if __name__ == "__main__":
    ejecutar_prueba()
