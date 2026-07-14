from SERVICIOS.flujo_diario_automatico_494 import generar_flujo_diario, formatear_flujo_diario


def main():
    datos = {
        "restaurante": "Boronat",
        "fecha": "hoy",
        "stock": [{"modulo": "stock", "descripcion": "Gambón bajo mínimos", "stock_actual": 1, "stock_minimo": 5}],
        "produccion": [{"modulo": "produccion", "descripcion": "Canelones pendientes", "produccion_bloqueada": True}],
        "eventos": [{"modulo": "eventos", "descripcion": "Evento 120 pax mañana", "evento_proximo": True}],
    }
    print(formatear_flujo_diario(generar_flujo_diario(datos)))


if __name__ == "__main__":
    main()
