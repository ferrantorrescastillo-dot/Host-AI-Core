from CORE.host_ai_core import HostAICore
from SERVICIOS.motor_intenciones_ia11 import MotorIntencionesIA11, ReglaIntencionIA11


def test_ia11_clasifica_intenciones_base_y_no_ejecuta(tmp_path):
    core = HostAICore(tmp_path)
    casos = {
        "Tengo una boda para 80 personas": "crear_evento",
        "¿Qué stock tengo?": "consultar_stock",
        "Necesito comprar tomates": "registrar_necesidad_compra",
        "Haz el pedido": "generar_pedido",
        "Crea una receta de ensaladilla": "crear_escandallo",
        "Calcula el coste de la carrillera": "calcular_costes",
        "Planifica la producción entre tres cocineros": "planificar_produccion",
        "Optimiza los recursos del horno": "optimizar_produccion",
    }
    for texto, esperado in casos.items():
        resultado = core.motor_intenciones_ia11.clasificar(texto)
        assert resultado["intent"] == esperado, (texto, resultado)
        assert resultado["confianza"] >= 0.55
        assert resultado["ejecutar"] is False
        assert resultado["version"] == "6.0.4-IA1.2"


def test_ia11_es_extensible_y_pide_aclaracion():
    motor = MotorIntencionesIA11()
    ambiguo = motor.clasificar("hola")
    assert ambiguo["intent"] == "conversacion_general"
    assert ambiguo["requiere_aclaracion"] is True

    motor.registrar_intencion(ReglaIntencionIA11(
        "hacer_inventario", "stock", "inventario", "motor_stock",
        ("haz inventario", "hacer inventario"), ("almacen",)
    ))
    resultado = motor.clasificar("Haz inventario del almacén")
    assert resultado["intent"] == "hacer_inventario"
    assert resultado["motor_sugerido"] == "motor_stock"
