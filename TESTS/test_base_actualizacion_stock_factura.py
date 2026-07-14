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
    assert any(p["nombre"] == "base_actualizacion_stock_factura" for p in listado.datos["pipelines"])

    relacion = {
        "articulo_id": "ART-CARRILLERA",
        "nombre_articulo": "Carrillera de ternera",
        "cantidad": 8,
        "unidad": "kg",
        "precio_unitario": 8.45,
        "importe": 67.60,
        "proveedor_id": "PROV-MAKRO",
        "numero_factura": "F-1",
    }

    mov = core.orquestador.resolver(SolicitudHostAI("preparar_movimiento_stock_factura", {
        "relacion": relacion
    }))
    assert mov.ok is True
    assert mov.datos["cantidad"] == 8
    assert mov.datos["requiere_revision"] is False

    informe = core.orquestador.resolver(SolicitudHostAI("preparar_informe_stock_factura", {
        "informe_relaciones": {"relaciones": [relacion]}
    }))
    assert informe.ok is True
    assert informe.datos["total_movimientos"] == 1
    assert informe.datos["entradas_preparadas"] == 1

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_informe_stock_factura", {
        "informe": informe.datos,
        "nombre": "test_informe_stock_factura.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.6.1 Modelos Actualización Stock")
    print("Informe:", informe.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
