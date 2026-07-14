from SERVICIOS.gestor_datos_minimos_52 import GestorDatosMinimos52
from SERVICIOS.orquestador_inteligente_52 import OrquestadorInteligente52


def test_flujo_evento_datos_minimos():
    gestor = GestorDatosMinimos52()

    r1 = gestor.procesar("Tengo una boda para 180 personas el sábado")
    assert r1["gestionado"] is True
    assert r1["estado"] == "faltan_datos"
    assert r1["evento"]["pax"] == 180
    assert r1["evento"]["fecha"] == "sabado"
    assert r1["siguiente_campo"] == "hora_servicio"

    r2 = gestor.procesar("a las 13:30")
    assert r2["siguiente_campo"] == "tipo_menu"
    assert r2["evento"]["hora_servicio"] == "13:30"

    r3 = gestor.procesar("menú paella con aperitivos")
    assert r3["siguiente_campo"] == "lugar"
    assert r3["evento"]["tipo_menu"] is not None

    r4 = gestor.procesar("en una finca")
    assert r4["siguiente_campo"] == "restricciones"

    r5 = gestor.procesar("sin restricciones")
    assert r5["siguiente_campo"] == "objetivo"

    r6 = gestor.procesar("todo el flujo completo")
    assert r6["estado"] == "datos_completos"
    assert not r6["faltantes"]


def test_orquestador_52_evento_no_inventa():
    orq = OrquestadorInteligente52()
    r = orq.procesar("Tengo una boda para 180 personas el sábado y dime qué comprar")
    assert r["ok"] is True
    assert r["estado"] == "faltan_datos"
    assert "no inventar" in r["mensaje"].lower()
    assert "¿a qué hora" in r["mensaje"].lower()


def main():
    test_flujo_evento_datos_minimos()
    test_orquestador_52_evento_no_inventa()
    print("TEST OK 5.2 Datos mínimos y preguntas inteligentes")


if __name__ == "__main__":
    main()
