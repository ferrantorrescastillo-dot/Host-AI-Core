from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.conector_stock_real_553 import procesar_consulta_stock_real_553
from SERVICIOS.orquestador_inteligente_52 import OrquestadorInteligente52


def main():
    r = procesar_consulta_stock_real_553("¿Qué stock tienes de arroz bomba?", BASE_DIR)
    assert r["gestionado"] is True
    assert r["intencion"] == "consultar_stock_real"
    assert r["datos"]["encontrado"] is True
    item = r["datos"]["coincidencias"][0]
    assert item["articulo"] == "Arroz bomba"
    assert item["stock_actual"] == 60.0, item
    assert item["stock_minimo"] == 10.0
    assert item["estado"] == "STOCK CORRECTO"

    orq = OrquestadorInteligente52(BASE_DIR)
    rr = orq.procesar("¿Qué stock tienes de arroz bomba?")
    assert rr["intencion"] == "consultar_stock_real", rr
    assert "Stock actual: 60 kg" in rr["mensaje"]
    print("TEST OK 5.5.3 Conector Real de Stock")


if __name__ == "__main__":
    main()
