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
    relacion = {
        "articulo_id": "ART-CARRILLERA",
        "nombre_articulo": "Carrillera de ternera",
        "proveedor_id": "PROV-MAKRO",
        "unidad": "kg",
        "precio_unitario": 8.45,
        "numero_factura": "F-1",
        "fecha_factura": "08/07/2026",
    }

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "base_actualizacion_precios_factura" for p in listado.datos["pipelines"])

    cambio = core.orquestador.resolver(SolicitudHostAI("preparar_cambio_precio_factura", {
        "relacion": relacion,
        "precio_anterior": 8.00,
    }))
    assert cambio.ok is True
    assert cambio.datos["precio_nuevo"] == 8.45
    assert abs(cambio.datos["variacion_porcentaje"] - 5.62) < 0.02
    assert cambio.datos["requiere_revision"] is False

    informe = core.orquestador.resolver(SolicitudHostAI("preparar_informe_precios_factura", {
        "informe_relaciones": {"relaciones": [relacion]}
    }))
    assert informe.ok is True
    assert informe.datos["total_cambios"] == 1

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_informe_precios_factura", {
        "informe": informe.datos,
        "nombre": "test_informe_precios.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.5.1 Modelos Actualización Precios")
    print("Cambio:", cambio.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
