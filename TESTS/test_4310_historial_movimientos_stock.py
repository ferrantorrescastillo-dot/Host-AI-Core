import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.historial_movimientos_stock_4310 import HistorialMovimientosStock4310


def main():
    movimientos = [
        {
            "id_movimiento": "MOV00000001",
            "fecha_hora": "2026-07-09T10:00:00",
            "codigo": "ART000001",
            "articulo": "Arroz bomba",
            "tipo": "entrada",
            "cantidad": 10,
            "unidad": "kg",
            "motivo": "Compra Makro",
            "stock_antes": 0,
            "stock_despues": 10,
            "usuario": "test",
            "documento_relacionado": "PED000001",
        },
        {
            "id_movimiento": "MOV00000002",
            "fecha_hora": "2026-07-09T11:00:00",
            "codigo": "ART000001",
            "articulo": "Arroz bomba",
            "tipo": "salida",
            "cantidad": 3,
            "unidad": "kg",
            "motivo": "Producción paella",
            "stock_antes": 10,
            "stock_despues": 7,
            "usuario": "test",
            "documento_relacionado": "PROD000001",
        },
        {
            "id_movimiento": "MOV00000003",
            "fecha_hora": "2026-07-09T12:00:00",
            "codigo": "ART000002",
            "articulo": "Aceite",
            "tipo": "ajuste",
            "cantidad": 5,
            "unidad": "l",
            "motivo": "Inventario real",
            "stock_antes": 4,
            "stock_despues": 5,
            "usuario": "test",
            "documento_relacionado": None,
        },
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_mov = Path(tmpdir) / "stock_movimientos.json"
        ruta_txt = Path(tmpdir) / "historial.txt"
        ruta_mov.write_text(json.dumps(movimientos, ensure_ascii=False, indent=2), encoding="utf-8")

        historial = HistorialMovimientosStock4310(str(ruta_mov))

        informe = historial.consultar(codigo="ART000001")
        assert informe.total_movimientos == 3
        assert informe.movimientos_filtrados == 2
        assert informe.movimientos[0].id_movimiento == "MOV00000002"

        informe_tipo = historial.consultar(tipo="ajuste")
        assert informe_tipo.movimientos_filtrados == 1
        assert informe_tipo.movimientos[0].codigo == "ART000002"

        exportado = historial.exportar_txt(str(ruta_txt), codigo="ART000001")
        assert exportado.movimientos_filtrados == 2
        assert ruta_txt.exists()

    print("TEST OK - Host AI 4.3.10 Historial Movimientos Stock")
    print("Filtro por código: OK")
    print("Filtro por tipo: OK")


if __name__ == "__main__":
    main()
