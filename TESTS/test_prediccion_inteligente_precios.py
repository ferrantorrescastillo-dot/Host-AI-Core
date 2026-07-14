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
    assert any(p["nombre"] == "prediccion_inteligente_precios" for p in listado.datos["pipelines"])

    precios = [8.0, 8.4, 8.8, 9.2, 9.8]
    for i, precio in enumerate(precios, 1):
        core.orquestador.resolver(SolicitudHostAI("registrar_precio_historico", {"registro": {
            "articulo_id": "ART-PRED-CARRILLERA", "nombre_articulo": "Carrillera test predicción",
            "precio": precio, "unidad": "kg", "proveedor_id": "PROV-PRED", "proveedor_nombre": "Proveedor Predicción",
            "numero_factura": f"F-PRED-{i}", "fecha_factura": f"2026-07-0{i}"
        }}))

    r = core.orquestador.resolver(SolicitudHostAI("predecir_precios_compras", {"ventana": 3}))
    assert r.ok is True
    assert r.datos["total_articulos"] >= 1
    pred = next(p for p in r.datos["predicciones"] if p["articulo_id"] == "ART-PRED-CARRILLERA")
    assert pred["media_movil"] > 0
    assert pred["prediccion_siguiente_precio"] >= pred["ultimo_precio"]
    assert pred["nivel_confianza"] in {"media", "alta"}

    uno = core.orquestador.resolver(SolicitudHostAI("predecir_precio_articulo", {"articulo_id": "ART-PRED-CARRILLERA", "ventana": 3}))
    assert uno.ok is True
    assert uno.datos["encontrado"] is True

    e = core.orquestador.resolver(SolicitudHostAI("exportar_prediccion_precios", {
        "prediccion": r.datos,
        "nombre": "test_prediccion_precios.json",
    }))
    assert e.ok is True
    assert Path(e.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.4.4 Predicción Inteligente Precios")
    print("Predicción OK:", pred["articulo_id"], pred["prediccion_siguiente_precio"], pred["nivel_confianza"])


if __name__ == "__main__":
    ejecutar_prueba()
