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
    assert any(p["nombre"] == "historico_inteligente_stock" for p in listado.datos["pipelines"])

    mov = {
        "articulo_id": "ART-CARRILLERA",
        "nombre_articulo": "Carrillera de ternera",
        "tipo": "entrada",
        "cantidad": 8,
        "unidad": "kg",
        "proveedor_id": "PROV-MAKRO",
        "numero_factura": "F-1",
    }
    r = core.orquestador.resolver(SolicitudHostAI("registrar_movimiento_stock_historico", {
        "movimiento": mov
    }))
    assert r.ok is True
    assert r.datos["registrado"] is True

    analisis = core.orquestador.resolver(SolicitudHostAI("analizar_historico_stock_articulo", {
        "articulo_id": "ART-CARRILLERA"
    }))
    assert analisis.ok is True
    assert analisis.datos["total_registros"] >= 1
    assert analisis.datos["entradas_totales"] >= 8

    lista = core.orquestador.resolver(SolicitudHostAI("listar_historico_stock", {}))
    assert lista.ok is True
    assert lista.datos["total"] >= 1

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_historico_stock", {}))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.6.3 Histórico Inteligente Stock")
    print("Análisis:", analisis.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
