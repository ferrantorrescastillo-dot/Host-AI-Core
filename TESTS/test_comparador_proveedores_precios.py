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

    for proveedor, precio in [("PROV-MAKRO", 8.45), ("PROV-BIDFOOD", 8.10), ("PROV-MAKRO", 8.35)]:
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
    assert any(p["nombre"] == "comparador_proveedores_precios" for p in listado.datos["pipelines"])

    comp = core.orquestador.resolver(SolicitudHostAI("comparar_proveedores_articulo", {
        "articulo_id": "ART-CARRILLERA"
    }))
    assert comp.ok is True
    assert comp.datos["mejor_proveedor"]["proveedor_id"] == "PROV-BIDFOOD"
    assert comp.datos["peor_proveedor"]["proveedor_id"] == "PROV-MAKRO"
    assert comp.datos["ahorro_potencial_unitario"] > 0

    todos = core.orquestador.resolver(SolicitudHostAI("comparar_proveedores_todos", {}))
    assert todos.ok is True
    assert todos.datos["total"] >= 1

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_comparacion_proveedores", {
        "comparacion": comp.datos,
        "nombre": "test_comparacion_proveedores.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.5.4 Comparador Proveedores Precios")
    print("Comparación:", comp.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
