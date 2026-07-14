from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI


def ejecutar_prueba():
    core = HostAICore(BASE_DIR)

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "detector_campos_linea_factura" for p in listado.datos["pipelines"])

    r = core.orquestador.resolver(SolicitudHostAI("detectar_campos_linea_factura", {
        "linea": "Aceite Oliva 5L 2 UD 39,90 79,80"
    }))
    assert r.ok is True
    assert r.datos["descripcion"] == "Aceite Oliva 5L"
    assert r.datos["cantidad"] == 2
    assert r.datos["unidad"] == "ud"
    assert round(r.datos["precio_unitario"], 2) == 39.90
    assert round(r.datos["importe"], 2) == 79.80
    assert r.datos["confianza"] >= 95

    lote = core.orquestador.resolver(SolicitudHostAI("detectar_campos_lote_factura", {
        "lineas": [
            "Carrillera Ternera 8 KG 8,45 67,60",
            "Cebolla 15 KG 1,12 16,80",
            "Texto no válido",
        ]
    }))
    assert lote.ok is True
    assert lote.datos["detectadas"] == 2

    texto = """
    Carrillera Ternera 8 KG 8,45 67,60
    Cebolla 15 KG 1,12 16,80
    """
    bloque = core.orquestador.resolver(SolicitudHostAI("leer_lineas_factura_texto", {
        "texto": texto
    }))
    assert bloque.ok is True
    assert bloque.datos["total_lineas"] == 2
    assert bloque.datos["confianza_media"] >= 95

    print("TEST OK - Host AI 3.0.3.3.3 Detector Cantidades Precios")
    print("Línea:", r.to_dict())
    print("Lote:", lote.to_dict())


if __name__ == "__main__":
    ejecutar_prueba()
