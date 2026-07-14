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
    assert any(p["nombre"] == "lector_completo_lineas_factura" for p in listado.datos["pipelines"])

    texto = """
    MAKRO ESPAÑA S.A.
    CIF A12345678
    Factura Nº F-2026-001
    Fecha 08/07/2026
    Carrillera Ternera 8 KG 8,45 67,60
    Cebolla 15 KG 1,12 16,80
    Aceite Oliva 5L 2 UD 39,90 79,80
    Base imponible 164,20
    IVA 16,42
    Total factura 180,62
    """

    r = core.orquestador.resolver(SolicitudHostAI("leer_factura_texto_completa", {
        "texto": texto,
        "proveedor_sugerido": "MAKRO ESPAÑA S.A.",
        "cif_sugerido": "A12345678",
        "numero_factura": "F-2026-001",
        "fecha_factura": "08/07/2026",
        "total_factura_detectado": 180.62,
    }))
    assert r.ok is True
    assert r.datos["total_lineas"] == 3
    assert r.datos["deteccion_proveedor"]["proveedor_id"] == "PROV-MAKRO"
    assert r.datos["lineas"][0]["descripcion"] == "Carrillera Ternera"

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_lectura_factura_completa", {
        "lectura": r.datos,
        "nombre": "test_lectura_factura_completa.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.3.4 Integración PDF Líneas")
    print("Lectura:", r.to_dict())


if __name__ == "__main__":
    ejecutar_prueba()
