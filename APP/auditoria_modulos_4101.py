from SERVICIOS.auditoria_modulos_4101 import auditar_modulos, formatear_auditoria_modulos


def main() -> None:
    print(formatear_auditoria_modulos(auditar_modulos()))


if __name__ == "__main__":
    main()
