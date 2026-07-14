from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path: sys.path.insert(0, str(BASE_DIR))
from CORE.host_ai_core import HostAICore
from CORE.orquestador import SolicitudHostAI

def cargar_datos(core):
    resultado = {"aplicado": True, "lectura_host_ai": "Importación demo cierre 304.", "preparacion": {"archivo":"factura_cierre_304.pdf", "ok": True, "requiere_revision": True, "lectura":{"proveedor_id":"PROV-A", "proveedor_nombre":"PROV-A", "total_lineas":3}, "relaciones":{"relacionadas_auto":2, "lineas":[{"articulo_id":"DESCONOCIDO", "descripcion":"Artículo sin relación", "confianza":0.1}]}}, "aplicacion_precios":{"aplicados":3}, "aplicacion_stock":{"aplicados":3}, "errores": [], "avisos":["OCR dudoso"]}
    core.orquestador.resolver(SolicitudHostAI("registrar_auditoria_importacion", {"resultado": resultado}))
    for prov, precios in {"PROV-A":[10,10.2,10.4,20,21], "PROV-B":[9.8,9.9,10.0,10.1]}.items():
        for precio in precios:
            core.orquestador.resolver(SolicitudHostAI("registrar_precio_historico", {"registro": {"articulo_id":"ART-ACEITE", "nombre_articulo":"Aceite", "precio":precio, "unidad":"l", "proveedor_id":prov, "proveedor_nombre":prov}}))
    for tipo,cantidad in [("entrada",20),("salida",5),("salida",4),("salida",6),("salida",5)]:
        core.orquestador.resolver(SolicitudHostAI("registrar_movimiento_stock_historico", {"movimiento": {"articulo_id":"ART-ACEITE", "nombre_articulo":"Aceite", "tipo":tipo, "cantidad":cantidad, "unidad":"l", "proveedor_id":"PROV-A"}}))

def ejecutar_prueba():
    core = HostAICore(BASE_DIR); core.memoria.limpiar_memoria(); cargar_datos(core)
    r = core.orquestador.resolver(SolicitudHostAI("comprobar_cierre_inteligencia_compras", {}))
    assert r.ok is True
    assert r.datos["ok_global"] is True
    assert r.datos["modulos_validados"] == 7
    print("TEST OK - Host AI 3.0.4.8 Cierre Inteligencia de Compras")
    print("Módulos validados:", r.datos["modulos_validados"], "/", r.datos["total_modulos"])

if __name__ == "__main__": ejecutar_prueba()
