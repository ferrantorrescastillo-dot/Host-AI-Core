from SERVICIOS.flujo_diario_automatico_494 import generar_flujo_diario, formatear_flujo_diario


def main():
    flujo = generar_flujo_diario({
        "restaurante": "Boronat",
        "stock": [{"modulo": "stock", "descripcion": "Arroz bajo", "stock_actual": 2, "stock_minimo": 10}],
        "produccion": [{"modulo": "produccion", "descripcion": "Fondo bloqueado", "produccion_bloqueada": True}],
        "eventos": [{"modulo": "eventos", "descripcion": "Boda mañana", "evento_proximo": True}],
    })
    assert flujo["total_tareas"] == 3
    assert flujo["compras"]
    assert flujo["produccion"]
    texto = formatear_flujo_diario(flujo)
    assert "FLUJO DIARIO" in texto
    assert "Boronat" in texto
    print("TEST OK 4.9.4 Flujo diario automático")


if __name__ == "__main__":
    main()
