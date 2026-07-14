from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from SERVICIOS.gestor_precio_venta_rentabilidad_555b732 import GestorPrecioVentaRentabilidad555B732


def main() -> int:
    texto = " ".join(sys.argv[1:]).strip()
    if not texto:
        print('Uso: python APP/gestionar_precio_venta_555b732.py "Pon un precio de venta de 9,50 € para ensaladilla de gamba"')
        return 2
    resultado = GestorPrecioVentaRentabilidad555B732(RAIZ).procesar(texto)
    print(resultado.get("mensaje", "Consulta no gestionada."))
    return 0 if resultado.get("gestionado") else 1


if __name__ == "__main__":
    raise SystemExit(main())
