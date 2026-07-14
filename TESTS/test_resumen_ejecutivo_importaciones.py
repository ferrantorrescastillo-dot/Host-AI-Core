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

    resultado = {
        "aplicado": True,
        "lectura_host_ai": "Importación ejecutada demo.",
        "preparacion": {
            "archivo": "demo.pdf",
            "ok": True,
            "lectura": {
                "proveedor_id": "PROV-MAKRO",
                "proveedor_nombre": "Makro",
                "total_lineas": 2,
            },
            "relaciones": {
                "relacionadas_auto": 2
            }
        },
        "aplicacion_precios": {"aplicados": 2},
        "aplicacion_stock": {"aplicados": 2},
        "errores": [],
        "avisos": [],
    }
    reg = core.orquestador.resolver(SolicitudHostAI("registrar_auditoria_importacion", {"resultado": resultado}))
    assert reg.ok is True

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "resumen_ejecutivo_importaciones" for p in listado.datos["pipelines"])

    resumen = core.orquestador.resolver(SolicitudHostAI("generar_resumen_importaciones", {}))
    assert resumen.ok is True
    assert resumen.datos["total_importaciones"] >= 1
    assert resumen.datos["aplicadas"] >= 1
    assert resumen.datos["total_lineas"] >= 2

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_resumen_importaciones", {
        "resumen": resumen.datos,
        "nombre": "test_resumen_importaciones.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.8.4 Resumen Ejecutivo Importaciones")
    print("Resumen OK:", resumen.datos["total_importaciones"], resumen.datos["aplicadas"])

if __name__ == "__main__":
    ejecutar_prueba()
