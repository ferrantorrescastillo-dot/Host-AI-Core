from SERVICIOS.auditoria_nucleo_ia_501 import ejecutar_auditoria_nucleo_ia


def main():
    resultado = ejecutar_auditoria_nucleo_ia()
    print(resultado["informe_texto"])


if __name__ == "__main__":
    main()
