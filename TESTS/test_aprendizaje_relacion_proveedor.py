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
        nombre="Carrillera de ternera",
        articulo_id="ART-CARRILLERA",
        unidad="kg",
        familia="carnes",
        proveedor="Makro",
        precio_unitario=8.45,
    )

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "aprendizaje_relacion_proveedor" for p in listado.datos["pipelines"])

    aprender = core.orquestador.resolver(SolicitudHostAI("aprender_relacion_proveedor_articulo", {
        "proveedor_id": "PROV-MAKRO",
        "texto_proveedor": "CARR TERN",
        "articulo_id": "ART-CARRILLERA",
        "nombre_articulo": "Carrillera de ternera",
        "confianza": 100,
    }))
    assert aprender.ok is True

    buscar = core.orquestador.resolver(SolicitudHostAI("buscar_aprendizaje_proveedor_articulo", {
        "proveedor_id": "PROV-MAKRO",
        "texto_proveedor": "CARR TERN",
    }))
    assert buscar.ok is True
    assert buscar.datos["aprendizaje"]["articulo_id"] == "ART-CARRILLERA"

    linea = {
        "descripcion": "CARR TERN",
        "cantidad": 8,
        "unidad": "kg",
        "precio_unitario": 8.45,
        "importe": 67.60,
    }
    rel = core.orquestador.resolver(SolicitudHostAI("relacionar_linea_articulo_factura", {
        "linea": linea,
        "proveedor_id": "PROV-MAKRO",
    }))
    assert rel.ok is True
    assert rel.datos["articulo_id"] == "ART-CARRILLERA"
    assert rel.datos["metodo"] == "aprendizaje_proveedor"
    assert rel.datos["requiere_revision"] is False

    listar = core.orquestador.resolver(SolicitudHostAI("listar_aprendizajes_proveedor_articulo", {}))
    assert listar.ok is True
    assert listar.datos["total"] >= 1

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_aprendizajes_proveedor_articulo", {}))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.4.4 Aprendizaje Proveedor Artículos")
    print("Relación:", rel.to_dict())


if __name__ == "__main__":
    ejecutar_prueba()
