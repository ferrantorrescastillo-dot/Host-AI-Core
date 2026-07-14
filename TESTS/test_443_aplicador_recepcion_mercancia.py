import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.aplicador_recepcion_mercancia_443 import AplicadorRecepcionMercancia443


def main():
    articulos = [
        {"codigo": "ART000001", "nombre": "Arroz bomba", "proveedor": "Makro", "familia": "Arroces", "precio": 3.0, "activo": True}
    ]
    stock = [
        {"codigo": "ART000001", "articulo": "Arroz bomba", "unidad": "kg", "stock_actual": 5, "stock_minimo": 2, "ubicacion": "Seco"}
    ]
    borrador = {
        "lineas_validadas": [
            {
                "producto_texto": "arroz bomba",
                "cantidad": 15,
                "unidad": "kg",
                "proveedor_texto": "Makro",
                "precio_unitario": 3.2,
                "codigo_articulo": "ART000001",
                "articulo_encontrado": "Arroz bomba",
                "proveedor_articulo": "Makro",
                "familia_articulo": "Arroces",
                "precio_actual_articulo": 3.0,
                "confianza": 0.95,
                "accion_sugerida": "entrada_stock",
                "mensajes": [],
            },
            {
                "producto_texto": "producto nuevo",
                "cantidad": 2,
                "unidad": "kg",
                "proveedor_texto": "Makro",
                "precio_unitario": 1.5,
                "codigo_articulo": None,
                "accion_sugerida": "crear_articulo_pendiente",
            },
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        db = Path(tmpdir)
        ruta_art = db / "articulos.json"
        ruta_stock = db / "stock_inicial.json"
        ruta_mov = db / "stock_movimientos.json"
        ruta_borrador = db / "recepcion_borrador.json"
        ruta_json = db / "aplicada.json"
        ruta_txt = db / "aplicada.txt"

        ruta_art.write_text(json.dumps(articulos, ensure_ascii=False, indent=2), encoding="utf-8")
        ruta_stock.write_text(json.dumps(stock, ensure_ascii=False, indent=2), encoding="utf-8")
        ruta_borrador.write_text(json.dumps(borrador, ensure_ascii=False, indent=2), encoding="utf-8")

        aplicador = AplicadorRecepcionMercancia443(str(ruta_borrador), str(ruta_stock), str(ruta_mov), str(ruta_art))
        resultado = aplicador.aplicar_y_exportar(str(ruta_json), str(ruta_txt))

        assert resultado.total_lineas == 2
        assert resultado.entradas_stock_ok == 1
        assert resultado.precios_actualizados == 1
        assert resultado.pendientes_articulo_nuevo == 1
        assert resultado.estado == "aplicado_con_pendientes"

        stock_final = json.loads(ruta_stock.read_text(encoding="utf-8"))
        assert stock_final[0]["stock_actual"] == 20

        articulos_final = json.loads(ruta_art.read_text(encoding="utf-8"))
        assert articulos_final[0]["precio"] == 3.2

        movimientos = json.loads(ruta_mov.read_text(encoding="utf-8"))
        assert len(movimientos) == 1
        assert movimientos[0]["tipo"] == "entrada"
        assert ruta_json.exists()
        assert ruta_txt.exists()

    print("TEST OK - Host AI 4.4.3 Aplicador Recepción Mercancía")
    print("Entradas stock OK:", resultado.entradas_stock_ok)
    print("Precios actualizados:", resultado.precios_actualizados)
    print("Pendientes nuevo:", resultado.pendientes_articulo_nuevo)


if __name__ == "__main__":
    main()
