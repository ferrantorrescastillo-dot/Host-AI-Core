from SERVICIOS.informe_financiero_inteligente_488 import generar_informe_financiero, formatear_informe_financiero


def main():
    datos = {"ventas": 4500, "coste_materia": 1450, "coste_personal": 1100, "mermas": 90, "otros_costes": 350}
    informe = generar_informe_financiero(datos)
    print(formatear_informe_financiero(informe))


if __name__ == "__main__":
    main()
