from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from SERVICIOS.conversacion_natural_5413 import resolver_referencia_natural_5413
from SERVICIOS.orquestador_inteligente_52 import OrquestadorInteligente52
acciones=[{"codigo":"evento","nombre":"Crear o localizar evento","modifica_datos":True},{"codigo":"menu","nombre":"Asociar menú del evento","modifica_datos":True},{"codigo":"compras","nombre":"Preparar compras necesarias","modifica_datos":False}]
ctx={"activo":True,"estado_conversacion":"esperando_seleccion_accion","confirmaciones":{"acciones_con_confirmacion":acciones},"accion_seleccionada":acciones[0]}
assert resolver_referencia_natural_5413("la segunda",ctx)["accion"]["codigo"]=="menu"
assert resolver_referencia_natural_5413("mejor la otra",ctx)["accion"]["codigo"]=="menu"
assert resolver_referencia_natural_5413("qué queda pendiente",ctx)["tipo"]=="consultar_pendientes"

o=OrquestadorInteligente52(BASE_DIR)
o.gestor_contexto_5410.activar_flujo({"flujo_pendiente_confirmacion":True,"estado_conversacion":"esperando_seleccion_accion","confirmaciones":{"acciones_con_confirmacion":acciones},"datos_flujo":{"tipo":"boda","personas":150},"flujo":{"pasos":[]}})
r=o.procesar("la segunda")
assert r["estado"]=="esperando_confirmacion_especifica",r
r=o.procesar("hazlo")
assert r["estado"]=="accion_confirmada_modo_seguro",r
r=o.procesar("qué queda pendiente")
assert r["estado"]=="pendientes_mostrados",r
assert "Crear o localizar evento" in r["mensaje"]
print("TEST OK 5.4.13 Conversacion Natural")
