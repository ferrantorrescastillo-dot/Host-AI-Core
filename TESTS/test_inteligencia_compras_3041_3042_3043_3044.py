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

    resultado = {
        "aplicado": True,
        "lectura_host_ai": "Importación demo bloque inteligencia compras.",
        "preparacion": {
            "archivo": "factura_pack_304_demo.pdf",
            "ok": True,
            "requiere_revision": True,
            "lectura": {"proveedor_id": "PROV-PACK", "proveedor_nombre": "Proveedor Pack", "total_lineas": 3},
            "relaciones": {"relacionadas_auto": 2, "lineas": [{"articulo_id": "DESCONOCIDO", "descripcion": "Artículo sin relación", "confianza": 0.1}]},
        },
        "aplicacion_precios": {"aplicados": 3},
        "aplicacion_stock": {"aplicados": 3},
        "errores": [],
        "avisos": ["OCR dudoso"],
    }
    core.orquestador.resolver(SolicitudHostAI("registrar_auditoria_importacion", {"resultado": resultado}))
    core.orquestador.resolver(SolicitudHostAI("registrar_auditoria_importacion", {"resultado": resultado}))

    for precio in [10, 10.2, 10.5, 20, 21]:
        core.orquestador.resolver(SolicitudHostAI("registrar_precio_historico", {"registro": {
            "articulo_id": "ART-PACK-ACEITE", "nombre_articulo": "Aceite pack inteligencia compras",
            "precio": precio, "unidad": "l", "proveedor_id": "PROV-PACK", "proveedor_nombre": "Proveedor Pack"
        }}))
    for cantidad in [4, 5, 6, 40]:
        core.orquestador.resolver(SolicitudHostAI("registrar_movimiento_stock_historico", {"movimiento": {
            "articulo_id": "ART-PACK-ACEITE", "nombre_articulo": "Aceite pack inteligencia compras",
            "tipo": "entrada", "cantidad": cantidad, "unidad": "l", "proveedor_id": "PROV-PACK"
        }}))

    analisis = core.orquestador.resolver(SolicitudHostAI("analizar_compras", {}))
    assert analisis.ok is True
    assert analisis.datos["total_importaciones"] >= 1

    recomendaciones = core.orquestador.resolver(SolicitudHostAI("generar_recomendaciones_compras", {}))
    assert recomendaciones.ok is True
    assert recomendaciones.datos["total"] >= 1

    anomalias = core.orquestador.resolver(SolicitudHostAI("detectar_anomalias_compras", {}))
    assert anomalias.ok is True
    assert anomalias.datos["total_anomalias"] >= 3

    prediccion = core.orquestador.resolver(SolicitudHostAI("predecir_precios_compras", {"ventana": 3}))
    assert prediccion.ok is True
    assert prediccion.datos["total_articulos"] >= 1
    assert any(p["articulo_id"] == "ART-PACK-ACEITE" for p in prediccion.datos["predicciones"])

    print("TEST OK - Host AI 3.0.4.1 + 3.0.4.2 + 3.0.4.3 + 3.0.4.4 Inteligencia de Compras")
    print("Analisis:", analisis.datos["total_importaciones"])
    print("Recomendaciones:", recomendaciones.datos["total"])
    print("Anomalias:", anomalias.datos["total_anomalias"])
    print("Predicciones:", prediccion.datos["total_articulos"])


if __name__ == "__main__":
    ejecutar_prueba()
