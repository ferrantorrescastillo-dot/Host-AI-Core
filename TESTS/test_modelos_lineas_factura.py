from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI
from MODELOS.lineas_factura import LineaFactura, BloqueLineasFactura


def ejecutar_prueba():
    linea = LineaFactura(
        descripcion="Carrillera de ternera",
        cantidad=8,
        unidad="kg",
        precio_unitario=8.45,
        importe=67.60,
        confianza=99,
    )
    assert linea.descripcion == "Carrillera de ternera"
    assert linea.to_dict()["importe"] == 67.60

    bloque = BloqueLineasFactura(
        proveedor_id="PROV-MAKRO",
        proveedor_nombre="Makro",
        total_factura_detectado=67.60,
        lineas=[linea],
    )
    datos_bloque = bloque.to_dict()
    assert datos_bloque["total_lineas"] == 1
    assert datos_bloque["total_importe_lineas"] == 67.60
    assert datos_bloque["diferencia_total"] == 0.0

    core = HostAICore(BASE_DIR)
    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "base_lineas_factura" for p in listado.datos["pipelines"])

    demo = core.orquestador.resolver(SolicitudHostAI("crear_bloque_lineas_factura_demo", {}))
    assert demo.ok is True
    assert demo.datos["total_lineas"] == 2

    validar = core.orquestador.resolver(SolicitudHostAI("validar_bloque_lineas_factura", {
        "bloque": demo.datos
    }))
    assert validar.ok is True

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_bloque_lineas_factura", {
        "bloque": demo.datos,
        "nombre": "test_bloque_lineas_factura.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.3.1 Modelos Líneas Factura")
    print("Bloque:", demo.to_dict())


if __name__ == "__main__":
    ejecutar_prueba()
