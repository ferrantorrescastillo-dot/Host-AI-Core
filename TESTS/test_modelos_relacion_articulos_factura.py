from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI
from MODELOS.relacion_articulos_factura import CandidatoArticuloFactura, RelacionLineaArticulo, InformeRelacionArticulosFactura


def ejecutar_prueba():
    candidato = CandidatoArticuloFactura("ART-CARRILLERA", "Carrillera de ternera", 96)
    relacion = RelacionLineaArticulo(
        descripcion_factura="CARR TERN",
        cantidad=8,
        unidad="kg",
        articulo_id="ART-CARRILLERA",
        nombre_articulo="Carrillera de ternera",
        confianza=96,
        requiere_revision=False,
        candidatos=[candidato],
    )
    informe = InformeRelacionArticulosFactura(relaciones=[relacion])
    datos = informe.to_dict()
    assert datos["total_lineas"] == 1
    assert datos["relacionadas_auto"] == 1
    assert datos["sin_relacion"] == 0
    assert datos["puede_continuar"] is True

    core = HostAICore(BASE_DIR)
    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "base_relacion_articulos_factura" for p in listado.datos["pipelines"])

    demo = core.orquestador.resolver(SolicitudHostAI("crear_informe_relacion_articulos_demo", {}))
    assert demo.ok is True
    assert demo.datos["total_lineas"] == 1

    validar = core.orquestador.resolver(SolicitudHostAI("validar_informe_relacion_articulos", {
        "informe": demo.datos,
    }))
    assert validar.ok is True

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_informe_relacion_articulos", {
        "informe": demo.datos,
        "nombre": "test_informe_relacion_articulos.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.4.1 Modelos Relación Artículos")
    print("Informe:", demo.to_dict())


if __name__ == "__main__":
    ejecutar_prueba()
