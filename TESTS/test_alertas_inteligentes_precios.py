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

    for proveedor, precio in [("PROV-MAKRO", 8.00), ("PROV-MAKRO", 9.00), ("PROV-BIDFOOD", 7.90)]:
        r = core.orquestador.resolver(SolicitudHostAI("registrar_precio_historico", {
            "registro": {
                "articulo_id": "ART-CARRILLERA",
                "nombre_articulo": "Carrillera de ternera",
                "precio": precio,
                "unidad": "kg",
                "proveedor_id": proveedor,
            }
        }))
        assert r.ok is True

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "alertas_inteligentes_precios" for p in listado.datos["pipelines"])

    alertas = core.orquestador.resolver(SolicitudHostAI("generar_alertas_precio_articulo", {
        "articulo_id": "ART-CARRILLERA"
    }))
    assert alertas.ok is True
    assert alertas.datos["total"] >= 1
    tipos = {a["tipo"] for a in alertas.datos["alertas"]}
    assert "oportunidad_ahorro" in tipos or "subida_fuerte" in tipos

    todas = core.orquestador.resolver(SolicitudHostAI("generar_alertas_precios_todos", {}))
    assert todas.ok is True
    assert todas.datos["total"] >= 1

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_alertas_precios", {}))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.5.5 Alertas Inteligentes Precios")
    print("Alertas:", alertas.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
