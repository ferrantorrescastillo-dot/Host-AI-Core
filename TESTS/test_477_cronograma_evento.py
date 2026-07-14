import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from SERVICIOS.cronograma_evento_477 import generar_cronograma_evento, agrupar_cronograma_por_dia, formatear_cronograma


def main():
    evento = {"id_evento": "EVT1", "fecha": "2026-08-01", "hora": "13:30", "personas": 180}
    cronograma = generar_cronograma_evento(evento, produccion=["fondos", "aperitivos", "paella"])
    assert cronograma["ok"] is True
    assert cronograma["total_tareas"] >= 8
    dias = agrupar_cronograma_por_dia(cronograma)
    assert "2026-08-01" in dias
    assert "CRONOGRAMA EVENTO" in formatear_cronograma(cronograma)
    print("TEST OK 4.7.7 Cronograma evento")


if __name__ == "__main__":
    main()
