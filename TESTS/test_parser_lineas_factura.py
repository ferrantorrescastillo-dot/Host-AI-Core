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
    assert any(p["nombre"] == "parser_lineas_factura" for p in listado.datos["pipelines"])

    texto = """
    MAKRO ESPAÑA S.A.
    Factura Nº F-2026-001
    Carrillera Ternera 8 KG 8,45 67,60
    Cebolla 15 KG 1,12 16,80
    Aceite Oliva 5L 2 UD 39,90 79,80
    Base imponible 164,20
    IVA 16,42
    Total factura 180,62
    """

    r = core.orquestador.resolver(SolicitudHostAI("leer_lineas_factura_texto", {
        "texto": texto,
        "proveedor_id": "PROV-MAKRO",
        "proveedor_nombre": "Makro",
        "numero_factura": "F-2026-001",
        "fecha_factura": "08/07/2026",
        "total_factura_detectado": 180.62,
    }))
    assert r.ok is True
    assert r.datos["total_lineas"] == 3

    lineas = r.datos["lineas"]
    assert lineas[0]["descripcion"] == "Carrillera Ternera"
    assert lineas[0]["cantidad"] == 8
    assert lineas[0]["unidad"] == "kg"
    assert round(lineas[0]["precio_unitario"], 2) == 8.45
    assert round(lineas[0]["importe"], 2) == 67.60

    assert lineas[2]["descripcion"] == "Aceite Oliva 5L"
    assert lineas[2]["cantidad"] == 2
    assert lineas[2]["unidad"] == "ud"
    assert round(lineas[2]["importe"], 2) == 79.80

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_lineas_factura", {
        "bloque": r.datos,
        "nombre": "test_lineas_factura_parser.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.3.2 Parser Líneas Factura")
    print("Resultado:", r.to_dict())


if __name__ == "__main__":
    ejecutar_prueba()
