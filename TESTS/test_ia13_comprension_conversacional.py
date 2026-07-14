from CORE.host_ai_core import HostAICore
from SERVICIOS.comprension_conversacional_ia13 import ComprensionConversacionalIA13


def test_ia13_completa_compra_en_dos_turnos(tmp_path):
    core = HostAICore(tmp_path)
    conversacion = core.comprension_conversacional_ia13

    primero = conversacion.procesar("Necesito comprar tomates", "compra")
    assert primero["intent"] == "registrar_necesidad_compra"
    assert primero["datos"]["articulo"] == "Tomates"
    assert primero["faltan"] == ["cantidad", "unidad"]
    assert "cantidad" in primero["pregunta"].lower()

    segundo = conversacion.procesar("5 kg", "compra")
    assert segundo["intent"] == "registrar_necesidad_compra"
    assert segundo["datos"]["articulo"] == "Tomates"
    assert segundo["datos"]["cantidad"] == 5
    assert segundo["datos"]["unidad"] == "kg"
    assert segundo["faltan"] == []
    assert segundo["estado"] == "comprendido"
    assert segundo["ejecutar"] is False


def test_ia13_completa_evento_con_respuesta_corta(tmp_path):
    core = HostAICore(tmp_path)
    conversacion = core.comprension_conversacional_ia13

    primero = conversacion.procesar("Tengo una boda", "evento")
    assert primero["intent"] == "crear_evento"
    assert "pax" in primero["faltan"]

    segundo = conversacion.procesar("para 80 personas mañana a las 13:30", "evento")
    assert segundo["datos"]["pax"] == 80
    assert segundo["datos"]["hora"] == "13:30"
    assert segundo["datos"]["tipo_evento"] == "boda"
    assert segundo["faltan"] == []
    assert segundo["requiere_aclaracion"] is False


def test_ia13_sinonimos_cocina_y_cancelacion():
    conversacion = ComprensionConversacionalIA13()
    ficha = conversacion.procesar("Crea una ficha de ensaladilla", "receta")
    assert ficha["intent"] == "crear_escandallo"
    assert ficha["datos"]["receta"] == "Ensaladilla"

    conversacion.procesar("Necesito comprar cebolla", "cancelar")
    cancelado = conversacion.procesar("cancelar", "cancelar")
    assert cancelado["estado"] == "cancelado"
    assert conversacion.obtener_estado("cancelar")["intent"] == ""


def test_ia13_sesiones_independientes_y_no_ejecuta():
    conversacion = ComprensionConversacionalIA13()
    a = conversacion.procesar("Necesito comprar arroz", "a")
    b = conversacion.procesar("Tengo una boda", "b")
    assert a["intent"] == "registrar_necesidad_compra"
    assert b["intent"] == "crear_evento"
    assert conversacion.obtener_estado("a")["datos"]["articulo"] == "Arroz"
    assert conversacion.obtener_estado("b")["datos"]["tipo_evento"] == "boda"
    assert a["ejecutar"] is False and b["ejecutar"] is False
