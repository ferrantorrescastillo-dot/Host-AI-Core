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
    assert any(p["nombre"] == "historico_inteligente_precios" for p in listado.datos["pipelines"])

    for precio, fecha in [(8.00, "01/01/2026"), (8.20, "01/02/2026"), (8.45, "01/03/2026")]:
        r = core.orquestador.resolver(SolicitudHostAI("registrar_precio_historico", {
            "registro": {
                "articulo_id": "ART-CARRILLERA",
                "nombre_articulo": "Carrillera de ternera",
                "precio": precio,
                "unidad": "kg",
                "proveedor_id": "PROV-MAKRO",
                "fecha_factura": fecha,
            }
        }))
        assert r.ok is True

    analisis = core.orquestador.resolver(SolicitudHostAI("analizar_historico_articulo", {
        "articulo_id": "ART-CARRILLERA"
    }))
    assert analisis.ok is True
    assert analisis.datos["total_registros"] == 3
    assert analisis.datos["precio_minimo"] == 8.0
    assert analisis.datos["precio_maximo"] == 8.45
    assert analisis.datos["tendencia"] == "sube"

    lista = core.orquestador.resolver(SolicitudHostAI("listar_historico_precios", {}))
    assert lista.ok is True
    assert lista.datos["total"] >= 3

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_historico_precios", {}))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.5.3 Histórico Inteligente Precios")
    print("Análisis:", analisis.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
