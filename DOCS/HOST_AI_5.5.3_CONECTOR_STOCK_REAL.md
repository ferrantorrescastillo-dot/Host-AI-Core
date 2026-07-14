# HOST AI 5.5.3 — Conector real de stock

## Objetivo
Responder consultas conversacionales de stock usando el inventario activo, sin quedarse en una promesa de ejecución.

## Fuentes reutilizadas
- `DATOS/db/stock_inicial.json`
- `DATOS/db/stock_movimientos.json`
- `DATOS/db/articulos.json`

## Comandos seguros
- `¿Qué stock tienes de arroz bomba?`
- `¿Cuánto stock queda de harina fuerza?`
- `Existencias de leche entera`

## Criterio
Si existe un movimiento posterior con `stock_despues`, prevalece sobre el valor inicial. Toda consulta es de solo lectura.
