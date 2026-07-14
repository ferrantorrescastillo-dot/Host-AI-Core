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
    assert any(p["nombre"] == "validador_lineas_factura" for p in listado.datos["pipelines"])

    linea_ok = {
        "descripcion": "Carrillera Ternera",
        "cantidad": 8,
        "unidad": "kg",
        "precio_unitario": 8.45,
        "importe": 67.60,
        "confianza": 100,
        "origen_texto": "Carrillera Ternera 8 KG 8,45 67,60",
    }
    v1 = core.orquestador.resolver(SolicitudHostAI("validar_linea_factura", {
        "linea": linea_ok
    }))
    assert v1.ok is True
    assert v1.datos["valida"] is True
    assert v1.datos["errores"] == []

    linea_mal = {
        "descripcion": "Aceite Oliva 5L",
        "cantidad": 2,
        "unidad": "ud",
        "precio_unitario": 39.90,
        "importe": 65.00,
        "confianza": 100,
    }
    v2 = core.orquestador.resolver(SolicitudHostAI("validar_linea_factura", {
        "linea": linea_mal
    }))
    assert v2.ok is False
    assert v2.datos["valida"] is False
    assert "El importe no coincide con cantidad x precio." in v2.datos["errores"]

    texto = """
    MAKRO ESPAÑA S.A.
    CIF A12345678
    Factura Nº F-2026-001
    Carrillera Ternera 8 KG 8,45 67,60
    Cebolla 15 KG 1,12 16,80
    Aceite Oliva 5L 2 UD 39,90 79,80
    Total factura 180,62
    """
    informe = core.orquestador.resolver(SolicitudHostAI("validar_factura_texto", {
        "texto": texto,
        "proveedor_sugerido": "MAKRO ESPAÑA S.A.",
        "cif_sugerido": "A12345678",
        "numero_factura": "F-2026-001",
        "total_factura_detectado": 180.62,
    }))
    assert informe.ok is True
    assert informe.datos["total_lineas"] == 3
    assert informe.datos["lineas_invalidas"] == 0
    assert informe.datos["puede_importar"] is True
    assert informe.datos["importe_lineas"] == 164.2
    assert len(informe.datos["avisos_generales"]) >= 1

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_validacion_factura", {
        "informe": informe.datos,
        "nombre": "test_validacion_factura.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.3.5 Validador Líneas Factura")
    print("Validación:", informe.to_dict())


if __name__ == "__main__":
    ejecutar_prueba()
