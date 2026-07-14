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

    mov = {
        "articulo_id": "ART-CARRILLERA",
        "nombre_articulo": "Carrillera de ternera",
        "cantidad": 8,
        "unidad": "kg",
        "proveedor_id": "PROV-MAKRO",
        "numero_factura": "F-REC-1",
        "requiere_revision": False,
    }

    aplicado = core.orquestador.resolver(SolicitudHostAI("aplicar_movimiento_stock_factura", {"movimiento": mov}))
    assert aplicado.ok is True

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "reconciliador_stock_factura" for p in listado.datos["pipelines"])

    rec = core.orquestador.resolver(SolicitudHostAI("reconciliar_movimiento_stock_factura", {"movimiento": mov}))
    assert rec.ok is True
    assert rec.datos["estado"] == "correcto"

    informe = core.orquestador.resolver(SolicitudHostAI("reconciliar_informe_stock_factura", {
        "informe_stock": {"movimientos": [mov]}
    }))
    assert informe.ok is True
    assert informe.datos["correctos"] == 1
    assert informe.datos["puede_cerrar_factura"] is True

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_reconciliacion_stock_factura", {
        "informe": informe.datos,
        "nombre": "test_reconciliacion_stock.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.6.5 Reconciliador Stock Factura")
    print("Informe:", informe.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
