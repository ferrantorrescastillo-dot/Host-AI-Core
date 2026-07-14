from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.confirmaciones_inteligentes_5412 import interpretar_confirmacion_contextual_5412
from SERVICIOS.orquestador_inteligente_52 import OrquestadorInteligente52

acciones = [
    {"codigo": "evento", "nombre": "Crear o localizar evento", "modifica_datos": True},
    {"codigo": "menu", "nombre": "Asociar menú del evento", "modifica_datos": True},
    {"codigo": "compras", "nombre": "Preparar compras necesarias", "modifica_datos": False},
]
ctx={"activo": True, "estado_conversacion": "esperando_seleccion_accion", "confirmaciones": {"acciones_con_confirmacion": acciones}}
assert interpretar_confirmacion_contextual_5412("aplica solo compras", ctx)["accion"]["codigo"] == "compras"
assert interpretar_confirmacion_contextual_5412("vuelve atrás", ctx)["tipo"] == "volver_seleccion"
ctx2={**ctx, "estado_conversacion": "esperando_confirmacion_especifica", "accion_seleccionada": acciones[1]}
assert interpretar_confirmacion_contextual_5412("adelante", ctx2)["tipo"] == "confirmar_accion"

o=OrquestadorInteligente52(BASE_DIR)
o.gestor_contexto_5410.activar_flujo({"flujo_pendiente_confirmacion": True, "estado_conversacion": "esperando_seleccion_accion", "confirmaciones": {"acciones_con_confirmacion": acciones}, "datos_flujo": {"tipo": "boda", "personas": 150}, "flujo": {"pasos": []}})
r=o.procesar("aplica solo compras")
assert r["estado"] == "accion_confirmada_modo_seguro", r
assert o.gestor_contexto_5410.esta_activo()
print("TEST OK 5.4.12 Confirmaciones Inteligentes")
