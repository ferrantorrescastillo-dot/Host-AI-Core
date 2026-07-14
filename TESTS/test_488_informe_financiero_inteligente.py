from SERVICIOS.informe_financiero_inteligente_488 import generar_informe_financiero, formatear_informe_financiero


def main():
    informe = generar_informe_financiero({"ventas": 1000, "coste_materia": 300, "coste_personal": 250, "mermas": 20, "otros_costes": 100})
    assert informe["beneficio"] == 330
    assert informe["margen"] == 0.33
    texto = formatear_informe_financiero(informe)
    assert "INFORME FINANCIERO" in texto
    assert "Beneficio" in texto
    print("TEST OK 4.8.8 Informe financiero inteligente")


if __name__ == "__main__":
    main()
