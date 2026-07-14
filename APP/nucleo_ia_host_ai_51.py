from SERVICIOS.nucleo_ia_host_ai_51 import procesar_solicitud_nucleo_ia


def main():
    print("=== HOST AI 5.1 - NUCLEO IA ===")
    solicitud = input("¿Qué necesitas? > ").strip()
    if not solicitud:
        solicitud = "Tengo una boda para 120 personas mañana y quiero organizar producción, compras y costes."
    resultado = procesar_solicitud_nucleo_ia(solicitud, {"restaurante": "Host AI"})
    print()
    print(resultado["respuesta"])


if __name__ == "__main__":
    main()
