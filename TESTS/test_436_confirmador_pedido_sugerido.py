import sys
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.confirmador_pedido_sugerido_436 import ConfirmadorPedidoSugerido436


def main():
    pedido_sugerido = {
        "pedidos_por_proveedor": [
            {
                "proveedor": "Makro",
                "lineas": [
                    {"codigo": "ART000001", "articulo": "Aceite", "unidad": "l", "cantidad_sugerida": 2, "prioridad": "alta"},
                    {"codigo": "ART000002", "articulo": "Arroz", "unidad": "kg", "cantidad_sugerida": 0, "prioridad": "media"},
                ],
            },
            {
                "proveedor": "Pau Gavalda",
                "lineas": [
                    {"codigo": "ART000003", "articulo": "Tomate", "unidad": "kg", "cantidad_sugerida": 4, "prioridad": "critica"},
                ],
            },
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_sug = Path(tmpdir) / "pedido_sugerido.json"
        ruta_conf = Path(tmpdir) / "pedidos_confirmados.json"
        ruta_sug.write_text(json.dumps(pedido_sugerido, ensure_ascii=False, indent=2), encoding="utf-8")

        confirmador = ConfirmadorPedidoSugerido436(str(ruta_sug), str(ruta_conf))
        resultado = confirmador.confirmar()

        assert resultado.pedidos_confirmados == 2
        assert resultado.lineas_confirmadas == 2
        assert resultado.estado == "confirmado"
        assert ruta_conf.exists()

        datos = json.loads(ruta_conf.read_text(encoding="utf-8"))
        assert len(datos) == 2
        assert datos[0]["id_pedido"] == "PED000001"
        assert datos[0]["proveedor"] == "Makro"

    print("TEST OK - Host AI 4.3.6 Confirmador Pedido Sugerido")
    print("Pedidos confirmados:", resultado.pedidos_confirmados)
    print("Líneas confirmadas:", resultado.lineas_confirmadas)


if __name__ == "__main__":
    main()
