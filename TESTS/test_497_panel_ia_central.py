from SERVICIOS.panel_ia_central_497 import generar_panel_ia_central, formatear_panel_ia_central


def main():
    panel = generar_panel_ia_central({
        "restaurante": "Boronat",
        "stock": [{"modulo": "stock", "descripcion": "Gambón bajo", "stock_actual": 1, "stock_minimo": 5, "horas_hasta_servicio": 10}],
        "produccion": [{"modulo": "produccion", "descripcion": "Fondo bloqueado", "produccion_bloqueada": True}],
        "eventos": [{"modulo": "eventos", "descripcion": "Boda mañana", "evento_proximo": True}],
    })
    assert panel["restaurante"] == "Boronat"
    assert panel["estado_general"] in {"estable", "atencion", "critico"}
    assert panel["total_alertas"] >= 1
    assert panel["siguiente_accion"] is not None
    texto = formatear_panel_ia_central(panel)
    assert "PANEL IA CENTRAL" in texto
    assert "Boronat" in texto
    print("TEST OK 4.9.7 Panel IA central")


if __name__ == "__main__":
    main()
