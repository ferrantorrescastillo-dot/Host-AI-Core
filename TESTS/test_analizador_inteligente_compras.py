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
        "lectura_host_ai": "Importación demo.",
        "preparacion": {
            "archivo": "demo.pdf",
            "ok": True,
            "lectura": {"proveedor_id": "PROV-MAKRO", "proveedor_nombre": "Makro", "total_lineas": 2},
            "relaciones": {"relacionadas_auto": 2}
        },
        "aplicacion_precios": {"aplicados": 2},
        "aplicacion_stock": {"aplicados": 2},
        "errores": [],
        "avisos": [],
    }
    core.orquestador.resolver(SolicitudHostAI("registrar_auditoria_importacion", {"resultado": resultado}))

    core.orquestador.resolver(SolicitudHostAI("registrar_movimiento_stock_historico", {"movimiento": {
        "articulo_id": "ART-CARRILLERA", "nombre_articulo": "Carrillera de ternera",
        "tipo": "entrada", "cantidad": 8, "unidad": "kg", "proveedor_id": "PROV-MAKRO"
    }}))
    core.orquestador.resolver(SolicitudHostAI("registrar_precio_historico", {"registro": {
        "articulo_id": "ART-CARRILLERA", "nombre_articulo": "Carrillera de ternera",
        "precio": 8.45, "unidad": "kg", "proveedor_id": "PROV-MAKRO"
    }}))

    listado = core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
    assert any(p["nombre"] == "analizador_inteligente_compras" for p in listado.datos["pipelines"])

    analisis = core.orquestador.resolver(SolicitudHostAI("analizar_compras", {}))
    assert analisis.ok is True
    assert analisis.datos["total_importaciones"] >= 1
    assert analisis.datos["total_lineas"] >= 2
    assert "ART-CARRILLERA" in analisis.datos["articulos"]

    exportar = core.orquestador.resolver(SolicitudHostAI("exportar_analisis_compras", {
        "analisis": analisis.datos,
        "nombre": "test_analisis_compras.json",
    }))
    assert exportar.ok is True
    assert Path(exportar.datos["archivo"]).exists()

    print("TEST OK - Host AI 3.0.4.1 Analizador Inteligente Compras")
    print("Analisis OK:", analisis.datos["total_importaciones"], len(analisis.datos["articulos"]))

if __name__ == "__main__":
    ejecutar_prueba()
