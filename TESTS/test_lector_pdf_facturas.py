from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def crear_pdf_demo(path: Path):
    try:
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(str(path))
        c.drawString(50, 800, "MAKRO ESPAÑA S.A.")
        c.drawString(50, 780, "CIF A12345678")
        c.drawString(50, 760, "Factura Nº F-2026-001")
        c.drawString(50, 740, "Fecha 08/07/2026")
        c.drawString(50, 700, "Carrillera de ternera 10 kg 8,50 85,00")
        c.drawString(50, 680, "Cebolla 5 kg 1,20 6,00")
        c.drawString(50, 640, "Base imponible 91,00")
        c.drawString(50, 620, "IVA 9,10")
        c.drawString(50, 600, "Total factura 100,10")
        c.save()
        return
    except Exception:
        pass

    # Fallback mínimo: si no hay reportlab, generamos un PDF simple con PyPDF2 no es trivial.
    # En ese caso saltamos con mensaje claro.
    raise RuntimeError("reportlab no está disponible para generar el PDF de prueba.")

def ejecutar_prueba():
    demo_path = BASE_DIR / "DATOS" / "facturas" / "factura_demo_makro.pdf"
    demo_path.parent.mkdir(parents=True, exist_ok=True)
    crear_pdf_demo(demo_path)

    core = HostAICore(BASE_DIR)
    core.memoria.limpiar_memoria()

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert listado.ok is True
    assert any(p["nombre"] == "pdf_facturas" for p in listado.datos["pipelines"])

    analisis = core.orquestador.resolver(SolicitudHostAI("analizar_pdf_factura", {
        "ruta_archivo": str(demo_path),
        "exportar_json": True,
    }))
    assert analisis.ok is True
    assert analisis.datos["total_paginas"] == 1
    assert analisis.datos["total_caracteres"] > 50
    assert "json_exportado" in analisis.datos

    det = analisis.datos["deteccion_factura"]
    assert det["proveedor"] == "MAKRO ESPAÑA S.A."
    assert det["numero_factura"]
    assert det["fecha"] == "08/07/2026"
    assert round(det["total"], 2) == 100.10
    assert det["confianza"] >= 70

    texto = """
    PROVEEDOR TEST
    Factura Nº FT-55
    Fecha 01/01/2026
    Base imponible 50,00
    IVA 5,00
    Total factura 55,00
    """
    det_texto = core.orquestador.resolver(SolicitudHostAI("detectar_factura_texto", {
        "texto": texto
    }))
    assert det_texto.ok is True
    assert round(det_texto.datos["total"], 2) == 55.00

    print("TEST OK - Host AI 3.0.3.1 Lector PDF Facturas")
    print("Análisis:", analisis.to_dict())
    print("Detección texto:", det_texto.to_dict())

if __name__ == "__main__":
    ejecutar_prueba()
