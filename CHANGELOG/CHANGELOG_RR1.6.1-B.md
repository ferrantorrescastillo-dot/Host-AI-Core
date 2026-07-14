# RR1.6.1-B — Compras y Recepción

## Correcciones

- Corrige el resumen roto de recepción que mostraba `Artículo: +- en seco`.
- El resultado de recepción incluye nombre, cantidad, unidad, ubicación, caducidad, coste, importe, lote y movimiento.
- Guarda el coste realmente recibido en la línea del pedido.
- Propone el último coste positivo conocido desde Stock cuando la línea del pedido no tiene precio.
- Avisa y exige confirmación adicional si se intenta recibir un pedido todavía en borrador.
- La cabecera de Compras separa necesidades pendientes sin pedido, necesidades ya vinculadas y pedidos abiertos.
- El resumen final confirma el estado del pedido, de las necesidades y del stock.

## Validación

- 97 pruebas superadas.
- 0 fallos.
- 0 errores de colección.
