import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from SERVICIOS.gestion_eventos_471 import crear_evento, validar_evento, guardar_evento, cargar_eventos, buscar_eventos, cambiar_estado_evento


def main():
    evento = crear_evento("Boda Ferran", "2026-08-01", "13:30", personas=180, cliente="Cliente A", lugar="Masia")
    assert validar_evento(evento)["ok"] is True
    evento2 = cambiar_estado_evento(evento, "confirmado")
    assert evento2["estado"] == "confirmado"
    with tempfile.TemporaryDirectory() as tmpdir:
        ruta = os.path.join(tmpdir, "eventos.json")
        res = guardar_evento(evento2, ruta)
        assert res["ok"] is True
        eventos = cargar_eventos(ruta)
        assert len(eventos) == 1
        assert buscar_eventos(eventos, texto="ferran")
    print("TEST OK 4.7.1 Gestion eventos")


if __name__ == "__main__":
    main()
