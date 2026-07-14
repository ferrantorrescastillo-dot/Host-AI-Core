from SERVICIOS.auditoria_tests_4102 import auditar_tests, formatear_auditoria_tests


def main() -> None:
    print(formatear_auditoria_tests(auditar_tests()))


if __name__ == "__main__":
    main()
