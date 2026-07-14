from SERVICIOS.auditoria_nucleo_ia_501 import ejecutar_auditoria_nucleo_ia


def main():
    resultado = ejecutar_auditoria_nucleo_ia()
    assert resultado["version"] == "5.0.1"
    assert resultado["total_casos"] >= 5
    assert resultado["casos_cubiertos"] >= 1  # El caso de evento ya debe funcionar.

    por_id = {r["id"]: r for r in resultado["resultados"]}
    assert por_id["evento_boda"]["cubierto_por_chat"] is True
    assert por_id["recepcion_mercancia_texto"]["modulos_disponibles"] is True
    assert por_id["recepcion_mercancia_texto"]["brecha"] is True
    assert resultado["casos_con_brecha"] >= 1
    assert "cuello de botella" in resultado["conclusion"].lower()
    print("TEST OK 5.0.1 Auditoría Núcleo IA")


if __name__ == "__main__":
    main()
