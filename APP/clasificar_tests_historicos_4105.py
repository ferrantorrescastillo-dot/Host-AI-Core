from SERVICIOS.clasificador_tests_historicos_4105 import clasificar_tests_historicos, formatear_clasificacion_tests


def main() -> None:
    resultado = clasificar_tests_historicos(".")
    print(formatear_clasificacion_tests(resultado))


if __name__ == "__main__":
    main()
