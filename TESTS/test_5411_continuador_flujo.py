from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.orquestador_inteligente_52 import OrquestadorInteligente52


def crear_orquestador_con_flujo():
    o = OrquestadorInteligente52(BASE_DIR)
    acciones = [
        {"codigo":"EVENTO_CREAR","nombre":"Crear o localizar evento","modifica_datos":True,"requiere_confirmacion":True},
        {"codigo":"MENU_ASOCIAR","nombre":"Asociar menú del evento","modifica_datos":True,"requiere_confirmacion":True},
        {"codigo":"COMPRAS_PREPARAR","nombre":"Preparar compras necesarias","modifica_datos":False,"requiere_confirmacion":True},
    ]
    flujo={"ok":True,"datos":{"tipo":"boda","personas":150,"fecha":"sabado","hora_servicio":"15:00","menu":"paella","lugar":"restaurante","restricciones":"sin restricciones","objetivo":"flujo completo"},"pasos":acciones}
    o.gestor_contexto_5410.activar_flujo({"flujo_pendiente_confirmacion":True,"datos_flujo":flujo["datos"],"flujo":flujo,"confirmaciones":{"acciones_con_confirmacion":acciones},"estado_conversacion":"pendiente_confirmacion"})
    o.contexto_activo_549=o.gestor_contexto_5410.contexto
    return o


def test_seleccionar_y_numero():
    o=crear_orquestador_con_flujo()
    r1=o.procesar("seleccionar")
    assert r1["estado"] == "seleccion_acciones_pendiente"
    assert o.gestor_contexto_5410.estado() == "esperando_seleccion_accion"
    r2=o.procesar("2")
    assert r2["intencion"] == "seleccion_flujo"
    assert "Asociar menú" in r2["mensaje"]
    assert "Conversación general" not in r2["mensaje"]
    assert o.gestor_contexto_5410.esta_activo()


def test_seleccion_por_nombre():
    o=crear_orquestador_con_flujo()
    o.procesar("seleccionar")
    r=o.procesar("preparar compras")
    assert "Preparar compras necesarias" in r["mensaje"]
    assert r["datos"]["resultado"]["modifico_datos_reales"] is False


if __name__ == "__main__":
    test_seleccionar_y_numero(); test_seleccion_por_nombre()
    print("TEST OK 5.4.11 Continuador Inteligente del Flujo")
