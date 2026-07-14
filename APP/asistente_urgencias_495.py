from SERVICIOS.asistente_urgencias_495 import detectar_urgencias, generar_resumen_urgencias


def main():
    situaciones = [
        {"modulo": "stock", "nombre": "Arroz bomba", "stock_actual": 2, "stock_necesario": 20, "horas_hasta_servicio": 18},
        {"modulo": "produccion", "nombre": "Fondo oscuro", "produccion_bloqueada": True},
        {"modulo": "eventos", "nombre": "Boda sábado 180 pax", "evento_proximo": True, "proveedor_no_confirmado": True},
    ]
    resultado = detectar_urgencias(situaciones)
    print(generar_resumen_urgencias(resultado))


if __name__ == "__main__":
    main()
