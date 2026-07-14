from SERVICIOS.nucleo_ia_host_ai_51 import (
    detectar_areas_solicitud,
    extraer_datos_basicos_solicitud,
    procesar_solicitud_nucleo_ia,
)


def main():
    solicitud = "Tengo una boda para 120 personas mañana y quiero saber qué producir, qué comprar y el coste."
    areas = detectar_areas_solicitud(solicitud)
    assert "eventos" in areas
    assert "produccion" in areas
    assert "stock" in areas
    assert "compras" in areas
    assert "rentabilidad" in areas

    datos = extraer_datos_basicos_solicitud(solicitud)
    assert datos["personas_estimadas"] == 120
    assert datos["urgente"] is True

    resultado = procesar_solicitud_nucleo_ia(solicitud, {
        "restaurante": "Boronat",
        "stock": [{"nombre": "Arroz", "stock_actual": 2, "stock_minimo": 10}],
        "compras": [{"nombre": "Gambón", "variacion_precio": 0.15}],
        "produccion": [{"nombre": "Fondo", "retraso_minutos": 45}],
        "rentabilidad": [{"nombre": "Paella", "margen": 0.18, "ventas": 20}],
    })
    assert resultado["estado"] == "ok"
    assert resultado["version"] == "5.1"
    assert resultado["plan"]["total_pasos"] >= 5
    assert "Modo seguro" in resultado["respuesta"]
    print("TEST OK 5.1 Núcleo IA Host AI")


if __name__ == "__main__":
    main()
