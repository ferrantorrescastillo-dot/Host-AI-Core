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
    assert any(p["nombre"] == "actualizador_inteligente_stock_factura" for p in listado.datos["pipelines"])

    movimiento = {
        "articulo_id": "ART-CARRILLERA",
        "nombre_articulo": "Carrillera de ternera",
        "cantidad": 8,
        "unidad": "kg",
        "proveedor_id": "PROV-MAKRO",
        "numero_factura": "F-1",
        "requiere_revision": False,
    }

    r = core.orquestador.resolver(SolicitudHostAI("aplicar_movimiento_stock_factura", {
        "movimiento": movimiento
    }))
    assert r.ok is True
    assert r.datos["aplicado"] is True

    stock = core.orquestador.resolver(SolicitudHostAI("consultar_stock_articulo_factura", {
        "articulo_id": "ART-CARRILLERA"
    }))
    assert stock.ok is True
    assert stock.datos["cantidad"] >= 8

    bloqueado = dict(movimiento)
    bloqueado["articulo_id"] = ""
    r2 = core.orquestador.resolver(SolicitudHostAI("aplicar_movimiento_stock_factura", {
        "movimiento": bloqueado
    }))
    assert r2.ok is False
    assert r2.datos["aplicado"] is False

    log = core.orquestador.resolver(SolicitudHostAI("listar_log_actualizacion_stock", {}))
    assert log.ok is True
    assert log.datos["total"] >= 2

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_log_actualizacion_stock", {}))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.6.2 Actualizador Inteligente Stock")
    print("Aplicación:", r.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
