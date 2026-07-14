from SERVICIOS.limpieza_apps_antiguas_4106 import analizar_apps_antiguas, formatear_limpieza_apps


def main() -> None:
    resultado = analizar_apps_antiguas(".")
    print(formatear_limpieza_apps(resultado))


if __name__ == "__main__":
    main()
