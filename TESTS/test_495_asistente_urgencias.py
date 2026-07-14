from SERVICIOS.asistente_urgencias_495 import detectar_urgencia, detectar_urgencias, generar_resumen_urgencias


def main():
    urgencia = detectar_urgencia({
        "modulo": "stock",
        "nombre": "Arroz bomba",
        "stock_actual": 2,
        "stock_necesario": 20,
        "horas_hasta_servicio": 12,
    })
    assert urgencia["prioridad"] in {"alta", "critica"}
    assert urgencia["requiere_confirmacion"] is True
    assert "stock" in urgencia["accion_principal"] or "compra" in urgencia["accion_principal"]

    resultado = detectar_urgencias([
        {"modulo": "stock", "nombre": "Arroz", "stock_actual": 1, "stock_minimo": 5},
        {"modulo": "produccion", "nombre": "Fondo", "produccion_bloqueada": True},
    ])
    assert resultado["total_urgencias"] == 2
    assert resultado["primera_accion"] is not None
    texto = generar_resumen_urgencias(resultado)
    assert "ASISTENTE DE URGENCIAS" in texto
    print("TEST OK 4.9.5 Asistente de urgencias")


if __name__ == "__main__":
    main()
