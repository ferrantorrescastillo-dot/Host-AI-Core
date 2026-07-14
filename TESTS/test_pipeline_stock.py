from pathlib import Path
import sys
from datetime import date, timedelta

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    if hasattr(core, "memoria"):
        core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "stock" for p in listado.datos["pipelines"])

    caducidad = (date.today() + timedelta(days=2)).isoformat()

    entrada = core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {
        "nombre": "Carrillera de ternera",
        "cantidad": 10,
        "unidad": "kg",
        "familia": "carnes",
        "ubicacion": "Cámara 1",
        "proveedor": "Proveedor Carnes",
        "caducidad": caducidad,
        "coste_unitario": 8.5,
    }))
    assert entrada.ok is True

    minimo = core.orquestador.resolver(SolicitudHostAI("ajustar_minimo_stock", {
        "nombre": "Carrillera de ternera",
        "cantidad_minima": 7,
    }))
    assert minimo.ok is True

    consumo = core.orquestador.resolver(SolicitudHostAI("consumir_stock", {
        "nombre": "Carrillera de ternera",
        "cantidad": 4,
        "unidad": "kg",
        "motivo": "Producción carrillera evento",
    }))
    assert consumo.ok is True
    assert consumo.datos["cantidad_consumida"] == 4
    assert consumo.datos["cantidad_faltante"] == 0

    stock = core.orquestador.resolver(SolicitudHostAI("stock_actual", {}))
    assert stock.ok is True
    assert stock.datos["total_items"] == 1
    assert round(stock.datos["items"][0]["cantidad"], 2) == 6.0

    diagnostico = core.orquestador.resolver(SolicitudHostAI("diagnosticar_stock", {
        "dias_caducidad_alerta": 3
    }))
    assert diagnostico.ok is True
    assert diagnostico.requiere_aprobacion is True
    tipos = [a["tipo"] for a in diagnostico.datos["avisos"]]
    assert "bajo_stock" in tipos
    assert "caducidad_cercana" in tipos

    prediccion = core.orquestador.resolver(SolicitudHostAI("predecir_necesidad_stock", {
        "nombre": "Carrillera de ternera",
        "cantidad_necesaria": 9,
        "unidad": "kg",
    }))
    assert prediccion.ok is True
    assert prediccion.requiere_aprobacion is True
    assert prediccion.datos["cantidad_faltante"] == 3

    movimientos = core.orquestador.resolver(SolicitudHostAI("movimientos_stock", {}))
    assert movimientos.ok is True
    assert len(movimientos.datos["movimientos"]) == 2

    print("TEST OK - Host AI v1.0.3 Pipeline de Stock Inteligente")
    print("Diagnóstico:", diagnostico.to_dict())
    print("Predicción:", prediccion.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
