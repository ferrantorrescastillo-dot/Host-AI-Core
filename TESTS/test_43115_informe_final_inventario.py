import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.informe_final_inventario_43115 import InformeFinalInventario43115


def main():
    comparacion = {
        "lineas": [
            {"codigo": "ART000001", "estado": "ok", "unidad": "kg", "diferencia": 0},
            {"codigo": "ART000002", "estado": "faltante", "unidad": "kg", "diferencia": -2},
            {"codigo": "ART000003", "estado": "sobrante", "unidad": "l", "diferencia": 1},
        ]
    }

    movimientos = [
        {"id_movimiento": "MOV00000001", "tipo": "ajuste", "motivo": "Ajuste por inventario físico", "codigo": "ART000002"},
        {"id_movimiento": "MOV00000002", "tipo": "ajuste", "motivo": "Ajuste por inventario físico", "codigo": "ART000003"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_comp = Path(tmpdir) / "comparacion.json"
        ruta_mov = Path(tmpdir) / "movimientos.json"
        ruta_txt = Path(tmpdir) / "final.txt"

        ruta_comp.write_text(json.dumps(comparacion, ensure_ascii=False, indent=2), encoding="utf-8")
        ruta_mov.write_text(json.dumps(movimientos, ensure_ascii=False, indent=2), encoding="utf-8")

        informeador = InformeFinalInventario43115(str(ruta_comp), str(ruta_mov))
        informe = informeador.exportar_txt(str(ruta_txt))

        assert informe.total_contados == 3
        assert informe.ok == 1
        assert informe.faltantes == 1
        assert informe.sobrantes == 1
        assert informe.ajustes_aplicados == 2
        assert informe.estado_final == "inventario_cerrado"
        assert ruta_txt.exists()

    print("TEST OK - Host AI 4.3.11.5 Informe Final Inventario")
    print("Estado final:", informe.estado_final)


if __name__ == "__main__":
    main()
