# HOST AI 6.0.4 — RR1.3 Pulido de Stock y Compras

## Objetivo
Cerrar las incidencias reales detectadas en el flujo necesidad → pedido → recepción → stock.

## Cambios
- La necesidad activa y el pedido activo se mantienen entre operaciones.
- Enter reutiliza el elemento activo; número o ID permite cambiarlo.
- Editar una necesidad sincroniza su línea en pedidos en borrador o preparados.
- Cambiar proveedor en la necesidad actualiza el pedido editable vinculado.
- Marcar una necesidad como comprada o cancelada retira su línea de pedidos editables.
- Generar pedidos explica cuándo las necesidades pendientes ya están vinculadas a pedidos abiertos.
- El listado principal muestra necesidades pendientes y pedidos abiertos.
- El menú de pedidos muestra el pedido activo.
- La recepción muestra un resumen de las entradas aplicadas a stock.
- Se mantiene el bloqueo de doble recepción.

## Validación
- 83 pruebas superadas.
- 0 fallos.
- 0 errores de colección.
