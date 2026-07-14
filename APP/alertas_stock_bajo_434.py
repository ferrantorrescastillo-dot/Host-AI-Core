from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.alertas_stock_bajo_434 import AlertasStockBajo434


def main():
    ruta_stock = ROOT / "DATOS" / "db" / "stock_inicial.json"
    ruta_informe = ROOT / "DATOS" / "db" / "alertas_stock_bajo_4_3_4.txt"

    generador = AlertasStockBajo434(str(ruta_stock))
    informe = generador.exportar_txt(str(ruta_informe))

    print("HOST AI 4.3.4 - Alertas de Stock Bajo")
    print("Archivo generado:", ruta_informe)
    print("Registros stock:", informe.total_registros_stock)
    print("Alertas:", informe.total_alertas)
    print("Críticas:", informe.alertas_criticas)
    print("Altas:", informe.alertas_altas)
    print("Medias:", informe.alertas_medias)
    print("Estado:", informe.estado)
    print("")

    for alerta in informe.alertas:
        print(f"[{alerta.prioridad.upper()}] {alerta.articulo}: quedan {alerta.stock_actual} {alerta.unidad}, mínimo {alerta.stock_minimo}. Faltan {alerta.diferencia} {alerta.unidad}.")


if __name__ == "__main__":
    main()
