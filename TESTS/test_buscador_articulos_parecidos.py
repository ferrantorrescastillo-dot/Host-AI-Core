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

    # Cargamos catálogo interno de ejemplo.
    core.importador_articulos_excel.articulos["ART-CARRILLERA"] = ArticuloImportadoExcel(
        nombre="Carrillera de ternera",
        articulo_id="ART-CARRILLERA",
        unidad="kg",
        familia="carnes",
        proveedor="Makro",
        precio_unitario=8.45,
    )
    core.importador_articulos_excel.articulos["ART-CEBOLLA"] = ArticuloImportadoExcel(
        nombre="Cebolla",
        articulo_id="ART-CEBOLLA",
        unidad="kg",
        familia="verduras",
        proveedor="Makro",
        precio_unitario=1.12,
    )

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "buscador_articulos_parecidos" for p in listado.datos["pipelines"])

    r = core.orquestador.resolver(SolicitudHostAI("buscar_articulo_parecido", {
        "descripcion": "CARR TERN",
        "proveedor_id": "PROV-MAKRO",
        "limite": 5,
    }))
    assert r.ok is True
    assert r.datos["mejor_candidato"]["articulo_id"] == "ART-CARRILLERA"
    assert r.datos["mejor_candidato"]["confianza"] >= 70

    r2 = core.orquestador.resolver(SolicitudHostAI("buscar_articulo_parecido", {
        "descripcion": "Cebolla",
        "proveedor_id": "PROV-MAKRO",
        "limite": 5,
    }))
    assert r2.ok is True
    assert r2.datos["mejor_candidato"]["articulo_id"] == "ART-CEBOLLA"
    assert r2.datos["mejor_candidato"]["confianza"] >= 95

    lote = core.orquestador.resolver(SolicitudHostAI("buscar_articulos_parecidos_lote", {
        "lineas": [
            {"descripcion": "CARR TERN"},
            {"descripcion": "Cebolla"},
        ],
        "proveedor_id": "PROV-MAKRO",
    }))
    assert lote.ok is True
    assert lote.datos["con_candidatos"] == 2

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_busqueda_articulos_parecidos", {
        "resultado": lote.datos,
        "nombre": "test_busqueda_articulos_parecidos.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.4.2 Buscador Artículos Parecidos")
    print("Búsqueda:", r.to_dict())


if __name__ == "__main__":
    ejecutar_prueba()
