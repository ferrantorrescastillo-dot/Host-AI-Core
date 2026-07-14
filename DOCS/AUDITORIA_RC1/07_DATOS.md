# RC1.1.7 — Auditoría DATOS

## Carpeta revisada

`DATOS/`

## Estado

Buena filosofía, pero será una de las áreas más importantes para la evolución del producto.

La calidad de los datos determinará la calidad de las recomendaciones de Host AI.

## Lo que está bien

- Separación clara entre código y datos.
- El sistema gira alrededor del artículo, que debe ser la entidad central.
- Existen históricos y estructuras pensadas para compras, stock, proveedores y producción.
- El diseño permite que Host AI aprenda con el tiempo.

## Riesgos

- Si se trabaja demasiado por nombre de artículo, pueden aparecer duplicados.
- Puede haber diferencias de escritura: mayúsculas, acentos, nombres comerciales y nombres internos.
- Los históricos deben separarse y mantenerse limpios.
- Excel es útil para empezar, pero no debe ser la base definitiva si el producto crece.

## Recomendaciones RC1

1. No migrar todo a base de datos antes del piloto.
2. Introducir progresivamente identificador único interno para artículos.
3. Añadir estados de calidad del dato: verificado, pendiente, duplicado, sospechoso, obsoleto.
4. Documentar qué datos mínimos necesita un restaurante para empezar.
5. Preparar una futura migración progresiva a SQLite.

## Prioridad

Muy alta para evolución, pero no bloqueante para el primer piloto controlado.
