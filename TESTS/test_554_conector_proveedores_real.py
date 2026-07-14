from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.conector_proveedores_real_554 import procesar_consulta_proveedores_real_554
from SERVICIOS.orquestador_inteligente_52 import OrquestadorInteligente52


def main():
    r = procesar_consulta_proveedores_real_554("¿Qué proveedores venden arroz bomba?", BASE_DIR)
    assert r["gestionado"] is True
    assert r["datos"]["encontrado"] is True, r
    item = r["datos"]["coinccidencias"][0] if "coincidencias" not in r["datos"] else r["datos"]["coincidencias"][0]
    assert item["articulo"] == "Arroz bomba"
    assert item["proveedor"] == "Makro"
    assert item["precio"] == 2.15

    orq = OrquestadorInteligente52(BASE_DIR)
    rr = orq.procesar("¿Quién vende arroz bomba?")
    assert rr["intencion"] == "consultar_proveedores_reales", rr
    assert "Proveedor habitual: Makro" in rr["mensaje"]
    print("TEST OK 5.5.4 Conector Real de Proveedores")


if __name__ == "__main__":
    main()
