from SERVICIOS.cierre_tecnico_host_ai_4108 import generar_cierre_tecnico_host_ai_4, formatear_cierre_tecnico


def main() -> None:
    resultado = generar_cierre_tecnico_host_ai_4(".")
    print(formatear_cierre_tecnico(resultado))


if __name__ == "__main__":
    main()
