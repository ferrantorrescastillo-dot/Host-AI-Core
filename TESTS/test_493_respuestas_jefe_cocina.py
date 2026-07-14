from SERVICIOS.respuestas_jefe_cocina_493 import generar_respuesta_jefe_cocina, explicar_decisiones_como_jefe, respuesta_urgente


def main():
    texto = generar_respuesta_jefe_cocina({"prioridad": "critica", "modulo": "stock", "problema": "falta arroz", "accion": "comprar hoy", "motivos": ["evento mañana"]})
    assert "resolverlo ya" in texto
    assert "comprar hoy" in texto
    bloque = explicar_decisiones_como_jefe([{"prioridad": "alta", "descripcion": "fondo pendiente", "accion_recomendada": "empezar ahora"}])
    assert "CRITERIO OPERATIVO" in bloque
    assert "Prioridad máxima" in respuesta_urgente("Falta arroz", "comprar 20 kg")
    print("TEST OK 4.9.3 Respuestas tipo jefe de cocina")


if __name__ == "__main__":
    main()
