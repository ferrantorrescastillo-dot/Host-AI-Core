# HOST AI 5.5.6CD.1 — Enlace canónico producción–stock

## Objetivo

Corregir el cruce de necesidades de producción con el inventario real mediante el `articulo_id` canónico, evitando depender únicamente del texto del ingrediente.

## Prioridad de búsqueda

1. Código/ID exacto del artículo.
2. Nombre exacto normalizado.
3. Coincidencia contenida única.
4. Coincidencia aproximada fuerte y no ambigua.

## Estados

- `STOCK_CORRECTO`: el inventario cubre la necesidad y mantiene el mínimo.
- `CUBRE_PERO_BAJO_MINIMO`: cubre la producción, pero deja el artículo bajo el mínimo.
- `STOCK_INSUFICIENTE`: hay inventario, pero no alcanza.
- `SIN_STOCK`: el inventario existe con cantidad cero.
- `ARTICULO_SIN_INVENTARIO`: el artículo existe en catálogo, pero aún no tiene registro de existencias.
- `ARTICULO_NO_LOCALIZADO`: no se ha podido enlazar el ingrediente con el catálogo.
- `UNIDAD_INCOMPATIBLE`: no se puede convertir la unidad de stock a la unidad requerida.

## Seguridad

La fase es de solo lectura. No descuenta stock, no crea movimientos y no genera pedidos.
