from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.confirmador_pedido_sugerido_436 import ConfirmadorPedidoSugerido436


def main():
    ruta_sugerido = ROOT / "DATOS" / "db" / "pedido_sugerido_stock_bajo_4_3_5.json"
    ruta_confirmados = ROOT / "DATOS" / "db" / "pedidos_confirmados.json"

    confirmador = ConfirmadorPedidoSugerido436(str(ruta_sugerido), str(ruta_confirmados))
    resultado = confirmador.confirmar()

    print("HOST AI 4.3.6 - Confirmar Pedido Sugerido")
    print("Pedidos confirmados:", resultado.pedidos_confirmados)
    print("Líneas confirmadas:", resultado.lineas_confirmadas)
    print("Archivo generado:", resultado.ruta_destino)
    print("Estado:", resultado.estado)
    print("Mensaje:", resultado.mensaje)


if __name__ == "__main__":
    main()
