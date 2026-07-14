from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria()
    resultado = {"aplicado": True, "lectura_host_ai": "Importación demo 304 completo.", "preparacion": {"archivo":"factura_3045_3046.pdf", "ok": True, "requiere_revision": True, "lectura":{"proveedor_id":"PROV-A", "proveedor_nombre":"PROV-A", "total_lineas":3}, "relaciones":{"relacionadas_auto":2, "lineas":[{"articulo_id":"DESCONOCIDO", "descripcion":"Artículo sin relación", "confianza":0.1}]}}, "aplicacion_precios":{"aplicados":3}, "aplicacion_stock":{"aplicados":3}, "errores": [], "avisos":["OCR dudoso"]}
    core.orquestador.resolver(SolicitudHostAI("registrar_auditoria_importacion", {"resultado": resultado}))
    core.orquestador.resolver(SolicitudHostAI("registrar_auditoria_importacion", {"resultado": resultado}))
    for prov, precios in {"PROV-A":[10,10.2,10.4,20,21], "PROV-B":[9.8,9.9,10.0,10.1]}.items():
        for precio in precios:
            core.orquestador.resolver(SolicitudHostAI("registrar_precio_historico", {"registro": {"articulo_id":"ART-ACEITE", "nombre_articulo":"Aceite", "precio":precio, "unidad":"l", "proveedor_id":prov, "proveedor_nombre":prov}}))
    for tipo,cantidad in [("entrada",20),("salida",5),("salida",4),("salida",6),("salida",5)]:
        core.orquestador.resolver(SolicitudHostAI("registrar_movimiento_stock_historico", {"movimiento": {"articulo_id":"ART-ACEITE", "nombre_articulo":"Aceite", "tipo":tipo, "cantidad":cantidad, "unidad":"l", "proveedor_id":"PROV-A"}}))
    analisis = core.orquestador.resolver(SolicitudHostAI("analizar_compras", {})); assert analisis.ok
    recomendaciones = core.orquestador.resolver(SolicitudHostAI("generar_recomendaciones_compras", {})); assert recomendaciones.ok
    anomalias = core.orquestador.resolver(SolicitudHostAI("detectar_anomalias_compras", {})); assert anomalias.ok
    prediccion = core.orquestador.resolver(SolicitudHostAI("predecir_precios_compras", {"ventana":3})); assert prediccion.ok
    comparador = core.orquestador.resolver(SolicitudHostAI("comparar_inteligente_proveedores_compras", {})); assert comparador.ok
    roturas = core.orquestador.resolver(SolicitudHostAI("predecir_roturas_stock", {"horizonte_dias":14})); assert roturas.ok
    assert comparador.datos["total_proveedores"] >= 2
    assert roturas.datos["total_articulos"] >= 1
    print("TEST OK - Host AI 3.0.4.1 + 3.0.4.2 + 3.0.4.3 + 3.0.4.4 + 3.0.4.5 + 3.0.4.6 Inteligencia de Compras")
    print("Analisis:", analisis.datos["total_importaciones"])
    print("Recomendaciones:", recomendaciones.datos["total"])
    print("Anomalias:", anomalias.datos["total_anomalias"])
    print("Predicciones precios:", prediccion.datos["total_articulos"])
    print("Proveedores comparados:", comparador.datos["total_proveedores"])
    print("Roturas stock:", roturas.datos["total_articulos"])

if __name__ == "__main__": ejecutar_prueba()
