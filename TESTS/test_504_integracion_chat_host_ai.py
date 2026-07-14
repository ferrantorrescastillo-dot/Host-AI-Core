from SERVICIOS.integracion_nucleo_ia_504 import ChatHostAIIntegrado504
from SERVICIOS.bootloader_host_ai_502 import BootloaderHostAI502


def main():
    chat = ChatHostAIIntegrado504()

    r = chat.responder("Han llegado 25 kg de arroz bomba de Makro a 2,15 €/kg.")
    assert r["intencion"] == "recepcion_mercancia", r
    assert r["datos"].get("stock_modificado") is False, r
    assert "borrador" in r["datos"], r
    assert "No he modificado stock" in r["mensaje"], r

    r2 = chat.responder("¿Qué tengo que comprar para mañana?")
    assert r2["intencion"] == "compras", r2

    boot = BootloaderHostAI502()
    opcion1 = boot.buscar_opcion("1")
    assert opcion1 is not None
    assert opcion1.destino == "APP.chat_host_ai_504", opcion1

    print("TEST OK 5.0.4 Integración Chat Host AI")


if __name__ == "__main__":
    main()
