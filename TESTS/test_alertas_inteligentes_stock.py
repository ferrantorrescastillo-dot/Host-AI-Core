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
        "tipo": "entrada",
        "cantidad": 3,
        "unidad": "kg",
        "proveedor_id": "PROV-MAKRO",
    }
    reg = core.orquestador.resolver(SolicitudHostAI("registrar_movimiento_stock_historico", {
        "movimiento": mov
    }))
    assert reg.ok is True

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "alertas_inteligentes_stock" for p in listado.datos["pipelines"])

    alerta = core.orquestador.resolver(SolicitudHostAI("generar_alertas_stock_articulo", {
        "articulo_id": "ART-CARRILLERA",
        "stock_minimo": 999
    }))
    assert alerta.ok is True
    assert alerta.datos["total"] >= 1
    tipos = {a["tipo"] for a in alerta.datos["alertas"]}
    assert "stock_bajo" in tipos or "sin_stock" in tipos or "sin_historico" in tipos

    todas = core.orquestador.resolver(SolicitudHostAI("generar_alertas_stock_todos", {
        "stock_minimo": 999
    }))
    assert todas.ok is True
    assert todas.datos["total"] >= 1

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_alertas_stock", {}))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.6.4 Alertas Inteligentes Stock")
    print("Alertas:", alerta.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
