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
    assert any(p["nombre"] == "detector_anomalias_compras" for p in listado.datos["pipelines"])

    # Histórico con subida fuerte, bajada sospechosa y precio no válido.
    for precio in [10.0, 10.5, 22.0, 7.0, 0.0]:
        core.orquestador.resolver(SolicitudHostAI("registrar_precio_historico", {"registro": {
            "articulo_id": "ART-ANOM-CARRILLERA", "nombre_articulo": "Carrillera test anomalías",
            "precio": precio, "unidad": "kg", "proveedor_id": "PROV-TEST", "proveedor_nombre": "Proveedor Test",
            "numero_factura": f"F-ANOM-{precio}", "fecha_factura": "2026-07-08"
        }}))

    # Stock con cantidad fuera de rango.
    for cantidad in [5, 6, 80]:
        core.orquestador.resolver(SolicitudHostAI("registrar_movimiento_stock_historico", {"movimiento": {
            "articulo_id": "ART-ANOM-CARRILLERA", "nombre_articulo": "Carrillera test anomalías",
            "tipo": "entrada", "cantidad": cantidad, "unidad": "kg", "proveedor_id": "PROV-TEST"
        }}))

    # Auditoría duplicada y con aviso OCR/artículo desconocido.
    resultado = {
        "aplicado": True,
        "lectura_host_ai": "Factura test anomalías aplicada con aviso OCR.",
        "preparacion": {
            "archivo": "factura_anomalia_demo.pdf",
            "ok": True,
            "requiere_revision": True,
            "lectura": {"proveedor_id": "PROV-TEST", "proveedor_nombre": "Proveedor Test", "total_lineas": 2},
            "relaciones": {"relacionadas_auto": 1, "lineas": [{"articulo_id": "DESCONOCIDO", "descripcion": "Producto OCR dudoso", "confianza": 0.2}]}
        },
        "aplicacion_precios": {"aplicados": 1},
        "aplicacion_stock": {"aplicados": 1},
        "errores": [],
        "avisos": ["OCR dudoso en una línea"],
    }
    core.orquestador.resolver(SolicitudHostAI("registrar_auditoria_importacion", {"resultado": resultado}))
    core.orquestador.resolver(SolicitudHostAI("registrar_auditoria_importacion", {"resultado": resultado}))

    r = core.orquestador.resolver(SolicitudHostAI("detectar_anomalias_compras", {}))
    assert r.ok is True
    assert r.datos["total_anomalias"] >= 4
    tipos = {a["tipo"] for a in r.datos["anomalias"]}
    assert "subida_anormal_precio" in tipos
    assert "factura_duplicada" in tipos
    assert "error_ocr_detectable" in tipos
    assert "cantidad_fuera_de_rango" in tipos

    e = core.orquestador.resolver(SolicitudHostAI("exportar_anomalias_compras", {
        "informe": r.datos,
        "nombre": "test_anomalias_compras.json",
    }))
    assert e.ok is True
    assert Path(e.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.4.3 Detector Anomalías Compras")
    print("Anomalías OK:", r.datos["total_anomalias"], r.datos["resumen_por_tipo"])


if __name__ == "__main__":
    ejecutar_prueba()
