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
        nombre="Carrillera de ternera", articulo_id="ART-CARRILLERA", unidad="kg", familia="carnes"
    )

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "validador_relaciones_articulos_factura" for p in listado.datos["pipelines"])

    relacion = {
        "descripcion_factura": "CARR TERN",
        "articulo_id": "ART-CARRILLERA",
        "nombre_articulo": "Carrillera de ternera",
        "confianza": 94,
        "metodo": "similitud_texto",
        "requiere_revision": False,
    }
    v = core.orquestador.resolver(SolicitudHostAI("validar_relacion_articulo_factura", {"relacion": relacion}))
    assert v.ok is True
    assert v.datos["valida"] is True

    mala = dict(relacion)
    mala["articulo_id"] = ""
    mala["confianza"] = 20
    v2 = core.orquestador.resolver(SolicitudHostAI("validar_relacion_articulo_factura", {"relacion": mala}))
    assert v2.ok is False
    assert v2.datos["valida"] is False

    informe = {
        "relaciones": [relacion]
    }
    inf = core.orquestador.resolver(SolicitudHostAI("validar_informe_relaciones_articulos", {"informe": informe}))
    assert inf.ok is True
    assert inf.datos["validas"] == 1
    assert inf.datos["puede_continuar"] is True

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_validacion_relaciones_articulos", {
        "informe": inf.datos, "nombre": "test_validacion_relaciones.json"
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.4.5 Validador Relaciones Artículos")
    print("Informe:", inf.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
