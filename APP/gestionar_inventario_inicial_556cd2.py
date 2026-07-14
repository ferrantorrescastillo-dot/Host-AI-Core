from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.inventario_inicial_seguro_556cd2 import (
    InventarioInicialSeguro556CD2,
    formatear_confirmacion_556cd2,
    formatear_faltantes_inventario_556cd2,
    formatear_propuesta_556cd2,
)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="HOST AI 5.5.6CD.2 - Inventario inicial seguro")
    p.add_argument("--listar-sin-inventario", action="store_true", help="Muestra artículos sin inventario")
    p.add_argument("--limite", type=int, default=30)
    p.add_argument("--articulo", help="Nombre o código exacto del artículo")
    p.add_argument("--cantidad", type=float, help="Cantidad real contada")
    p.add_argument("--unidad", help="kg, l, u, g o ml")
    p.add_argument("--ubicacion", help="Ubicación física")
    p.add_argument("--stock-minimo", type=float, help="Mínimo específico; si se omite usa la configuración recomendada")
    p.add_argument("--confirmar", action="store_true", help="Escribe el inventario inicial tras mostrar la propuesta")
    return p


def main() -> int:
    args = parser().parse_args()
    servicio = InventarioInicialSeguro556CD2(ROOT)

    if args.listar_sin_inventario:
        print(formatear_faltantes_inventario_556cd2(servicio.listar_sin_inventario(args.limite)))
        return 0

    if not args.articulo or args.cantidad is None:
        parser().error("Debes indicar --articulo y --cantidad, o usar --listar-sin-inventario")

    resultado = servicio.proponer(
        args.articulo,
        args.cantidad,
        unidad=args.unidad,
        ubicacion=args.ubicacion,
        stock_minimo=args.stock_minimo,
    )
    print(formatear_propuesta_556cd2(resultado))
    if not args.confirmar or not resultado.get("ok"):
        return 0 if resultado.get("ok") else 2

    confirmado = servicio.confirmar(resultado["propuesta"])
    print()
    print(formatear_confirmacion_556cd2(confirmado))
    return 0 if confirmado.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
