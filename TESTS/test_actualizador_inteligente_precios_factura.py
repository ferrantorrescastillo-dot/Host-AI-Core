from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI
from MODELOS.importacion_articulos_excel import ArticuloImportadoExcel

def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()
    core.importador_articulos_excel.articulos["ART-CARRILLERA"] = ArticuloImportadoExcel(
        nombre="Carrillera de ternera", articulo_id="ART-CARRILLERA", unidad="kg", precio_unitario=8.0
    )

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "actualizador_inteligente_precios_factura" for p in listado.datos["pipelines"])

    cambio = {
        "articulo_id": "ART-CARRILLERA",
        "nombre_articulo": "Carrillera de ternera",
        "proveedor_id": "PROV-MAKRO",
        "precio_anterior": 8.0,
        "precio_nuevo": 8.45,
        "unidad": "kg",
        "variacion_porcentaje": 5.62,
        "requiere_revision": False,
    }
    r = core.orquestador.resolver(SolicitudHostAI("aplicar_cambio_precio_factura", {"cambio": cambio}))
    assert r.ok is True
    assert r.datos["aplicado"] is True
    assert core.importador_articulos_excel.articulos["ART-CARRILLERA"].precio_unitario == 8.45

    fuerte = dict(cambio)
    fuerte["precio_nuevo"] = 15.0
    fuerte["variacion_porcentaje"] = 87.5
    bloqueado = core.orquestador.resolver(SolicitudHostAI("aplicar_cambio_precio_factura", {"cambio": fuerte}))
    assert bloqueado.ok is False
    assert bloqueado.datos["aplicado"] is False

    log = core.orquestador.resolver(SolicitudHostAI("listar_log_actualizacion_precios", {}))
    assert log.ok is True
    assert log.datos["total"] >= 2

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_log_actualizacion_precios", {}))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.5.2 Actualizador Inteligente Precios")
    print("Aplicación:", r.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
