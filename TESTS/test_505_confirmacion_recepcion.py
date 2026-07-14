from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from SERVICIOS.integracion_nucleo_ia_505 import ChatHostAIIntegrado505
from SERVICIOS.bootloader_host_ai_502 import BootloaderHostAI502


def _preparar_base_temporal() -> Path:
    origen = Path.cwd() / "DATOS" / "db"
    tmp = Path(tempfile.mkdtemp(prefix="host_ai_505_"))
    destino = tmp / "DATOS" / "db"
    destino.mkdir(parents=True, exist_ok=True)
    for nombre in ["articulos.json", "stock_inicial.json"]:
        shutil.copy2(origen / nombre, destino / nombre)
    (destino / "stock_movimientos.json").write_text("[]", encoding="utf-8")
    return tmp


def main():
    base = _preparar_base_temporal()
    try:
        chat = ChatHostAIIntegrado505(base)
        r = chat.responder("Han llegado 25 kg de arroz bomba de Makro a 2,15 €/kg.")
        assert r["intencion"] == "recepcion_mercancia", r
        assert r["datos"].get("stock_modificado") is False, r
        assert "Makro" in r["mensaje"], r["mensaje"]
        assert "arroz bomba" in r["mensaje"].lower(), r["mensaje"]
        assert "¿Quieres aplicar" in r["mensaje"] or r["datos"].get("aplicables", 0) == 0, r["mensaje"]

        r2 = chat.responder("S")
        assert r2["intencion"] == "recepcion_mercancia", r2
        assert "Recepción procesada" in r2["mensaje"], r2["mensaje"]
        datos = r2["datos"].get("resultado_aplicacion", {})
        assert "entradas_stock_ok" in datos, r2

        # Debe haber dejado archivos de aplicación, aunque algunas líneas puedan quedar pendientes por revisión.
        assert (base / "DATOS" / "db" / "recepcion_borrador_4_4_2.json").exists()
        assert (base / "DATOS" / "db" / "recepcion_aplicada_4_4_3.json").exists()

        boot = BootloaderHostAI502(base)
        assert boot.buscar_opcion("1").destino == "APP.chat_host_ai_505"
        assert boot.buscar_opcion("7").destino == "TESTS.test_505_confirmacion_recepcion"
    finally:
        shutil.rmtree(base, ignore_errors=True)

    print("TEST OK 5.0.5 Confirmación y aplicación recepción")


if __name__ == "__main__":
    main()
