from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()
    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "proveedores_pdf" for p in listado.datos["pipelines"])

    texto_makro = """MAKRO ESPAÑA S.A.
CIF A12345678
Factura Nº F-2026-001
Fecha 08/07/2026
Total factura 100,10"""
    det = core.orquestador.resolver(SolicitudHostAI("detectar_proveedor_texto", {"texto": texto_makro, "proveedor_sugerido": "MAKRO ESPAÑA S.A.", "cif_sugerido": "A12345678"}))
    assert det.ok is True
    assert det.datos["proveedor_id"] == "PROV-MAKRO"
    assert det.datos["confianza"] >= 95

    texto_desconocido = """CARNES PEPITO SL
CIF B99887766
Factura CP-1
Total factura 50,00"""
    det2 = core.orquestador.resolver(SolicitudHostAI("detectar_proveedor_texto", {"texto": texto_desconocido, "proveedor_sugerido": "CARNES PEPITO SL", "cif_sugerido": "B99887766"}))
    assert det2.ok is True
    assert det2.datos["requiere_aprendizaje"] is True

    aprender = core.orquestador.resolver(SolicitudHostAI("aprender_proveedor_pdf", {"nombre": "Carnes Pepito", "proveedor_id": "PROV-CARNES-PEPITO", "cif": "B99887766", "palabras_clave": ["carnes pepito", "pepito"], "categoria": "carnes"}))
    assert aprender.ok is True
    det3 = core.orquestador.resolver(SolicitudHostAI("detectar_proveedor_texto", {"texto": texto_desconocido, "proveedor_sugerido": "CARNES PEPITO SL", "cif_sugerido": "B99887766"}))
    assert det3.ok is True
    assert det3.datos["proveedor_id"] == "PROV-CARNES-PEPITO"
    assert det3.datos["confianza"] >= 95

    lista = core.orquestador.resolver(SolicitudHostAI("listar_proveedores_pdf", {}))
    assert lista.ok is True
    assert lista.datos["total"] >= 6
    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_diccionario_proveedores_pdf", {}))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.3.2 Detector Proveedores PDF")
    print("Detección Makro:", det.to_dict())
    print("Detección aprendida:", det3.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
