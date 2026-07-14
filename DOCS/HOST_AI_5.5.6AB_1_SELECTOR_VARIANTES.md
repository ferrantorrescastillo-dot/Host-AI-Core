# Host AI 5.5.6AB.1 — Selector conversacional de variantes

## Objetivo

Cuando una receta tiene variantes reales pendientes de importación, Host AI no elige una al azar. Muestra las opciones con su origen y rendimiento, conserva el cálculo solicitado y permite continuar respondiendo con el número elegido.

## Ejemplo

`Desglosa la producción de Patatas bravas para 100 personas.`

Host AI muestra:

1. Patatas Bravas — Aperitivos
2. Patatas Bravas — BBQ

Al responder `2`, continúa el cálculo con la variante BBQ.

## Seguridad

- Las variantes se leen desde los informes de preimportación y resolución.
- La selección solo se usa para el cálculo actual.
- No se importan variantes, no se crean órdenes y no se descuenta stock.
