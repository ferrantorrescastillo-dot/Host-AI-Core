from SERVICIOS.panel_ia_central_497 import generar_panel_ia_central, formatear_panel_ia_central


def main():
    datos = {
        "restaurante": "Boronat",
        "fecha": "hoy",
        "stock": [{"modulo": "stock", "descripcion": "Arroz bajo mínimos", "nombre": "Arroz", "stock_actual": 2, "stock_minimo": 10}],
        "produccion": [{"modulo": "produccion", "descripcion": "Fondo oscuro bloqueado", "produccion_bloqueada": True}],
        "eventos": [{"modulo": "eventos", "descripcion": "Boda mañana 180 pax", "evento_proximo": True}],
        "rentabilidad": [{"modulo": "rentabilidad", "descripcion": "Paella con margen bajo", "nombre": "Paella", "margen": 0.18, "ventas": 40}],
    }
    print(formatear_panel_ia_central(generar_panel_ia_central(datos)))


if __name__ == "__main__":
    main()
