from SERVICIOS.motor_decisiones_operativas_491 import generar_decisiones_operativas, resumen_decisiones_operativas


def main():
    situaciones = [
        {"modulo": "stock", "descripcion": "Arroz bomba bajo mínimos", "stock_actual": 3, "stock_minimo": 10, "horas_hasta_servicio": 20},
        {"modulo": "produccion", "descripcion": "Fondo oscuro pendiente", "produccion_bloqueada": True, "horas_hasta_servicio": 30},
        {"modulo": "rentabilidad", "descripcion": "Canelón con margen bajo", "margen": 0.18},
    ]
    resultado = generar_decisiones_operativas(situaciones)
    print(resumen_decisiones_operativas(resultado))


if __name__ == "__main__":
    main()
