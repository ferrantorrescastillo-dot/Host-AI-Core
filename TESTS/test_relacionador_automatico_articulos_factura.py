from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI
from MODELOS.importacion_articulos_excel import ArticuloImportadoExcel


def cargar_catalogo(core):
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


def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()
    cargar_catalogo(core)

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "relacionador_automatico_articulos_factura" for p in listado.datos["pipelines"])

    linea = {
        "descripcion": "CARR TERN",
        "cantidad": 8,
        "unidad": "kg",
        "precio_unitario": 8.45,
        "importe": 67.60,
    }
    r = core.orquestador.resolver(SolicitudHostAI("relacionar_linea_articulo_factura", {
        "linea": linea,
        "proveedor_id": "PROV-MAKRO",
    }))
    assert r.ok is True
    assert r.datos["articulo_id"] == "ART-CARRILLERA"
    assert r.datos["requiere_revision"] is False

    bloque = {
        "proveedor_id": "PROV-MAKRO",
        "proveedor_nombre": "Makro",
        "numero_factura": "F-2026-001",
        "lineas": [
            {"descripcion": "CARR TERN", "cantidad": 8, "unidad": "kg", "precio_unitario": 8.45, "importe": 67.60},
            {"descripcion": "Cebolla", "cantidad": 15, "unidad": "kg", "precio_unitario": 1.12, "importe": 16.80},
        ]
    }
    inf = core.orquestador.resolver(SolicitudHostAI("relacionar_bloque_articulos_factura", {
        "bloque": bloque
    }))
    assert inf.ok is True
    assert inf.datos["total_lineas"] == 2
    assert inf.datos["relacionadas_auto"] == 2
    assert inf.datos["sin_relacion"] == 0

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_relacion_articulos_factura", {
        "informe": inf.datos,
        "nombre": "test_relacion_automatica_articulos.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.4.3 Relacionador Automático Artículos")
    print("Informe:", inf.to_dict())


if __name__ == "__main__":
    ejecutar_prueba()
