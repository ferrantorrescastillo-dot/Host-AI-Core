from SERVICIOS.mapa_maestro_modulos_4107 import generar_mapa_maestro, formatear_mapa_maestro


def main() -> None:
    resultado = generar_mapa_maestro(".")
    print(formatear_mapa_maestro(resultado))


if __name__ == "__main__":
    main()
