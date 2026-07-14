from SERVICIOS.respuestas_jefe_cocina_493 import generar_respuesta_jefe_cocina


def main():
    print(generar_respuesta_jefe_cocina({
        "prioridad": "alta",
        "modulo": "producción",
        "problema": "el fondo necesita 8 horas y el servicio es mañana",
        "accion": "empezar el fondo antes que tareas cortas",
        "motivos": ["tiempo pasivo largo", "dependencia de otras elaboraciones"],
    }))


if __name__ == "__main__":
    main()
