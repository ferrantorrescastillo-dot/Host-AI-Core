import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from SERVICIOS.informe_final_evento_478 import calcular_resultado_evento, generar_recomendaciones_evento, formatear_informe_final_evento


def main():
    evento = {"id_evento": "EVT1", "nombre": "Boda Ferran", "personas": 180, "presupuesto": 9000}
    costes = {"materia_prima": 2500, "personal": 1800, "transporte": 300, "material": 400}
    informe = calcular_resultado_evento(evento, costes)
    assert informe["ok"] is True
    assert informe["beneficio"] == 4000
    assert informe["margen_porcentaje"] > 40
    assert generar_recomendaciones_evento(informe)
    assert "INFORME FINAL EVENTO" in formatear_informe_final_evento(informe)
    print("TEST OK 4.7.8 Informe final evento")


if __name__ == "__main__":
    main()
