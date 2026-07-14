# I1.3.1 — Detector limpio de menús

## Objetivo
Separar la detección del menú de la vinculación e importación. Este sprint clasifica cada fila y genera una vista previa limpia, sin escribir en la base de datos.

## Incluye
- Clasificación de filas: título, cabecera, sección, plato, artículo directo, complemento, resumen económico, vacía y ruido.
- Exclusión de cabeceras como `GR O KG`, `PRECIO KG`, `EUROS/RACION`, `ESCANDALLO` y `Benefici`.
- `COCTEL BIENVENIDA...` reconocido como subsección, no como plato.
- `BODEGA, PAN, VINO Y CAFES` reconocido como complemento.
- `Pan individual rombo makro` reconocido como artículo directo.
- Lectura del coste por ración desde la columna identificada por `EUROS/RACION`, no desde la cantidad.
- Lectura de venta, venta neta, coste total, food cost y beneficio.
- Vista previa sin vinculación de recetas y sin método de importación.

## Compatibilidad
- El servicio certificado I1.3 anterior se conserva intacto como referencia legacy.
- La opción 11 de consola pasa a ejecutar únicamente I1.3.1.
- No se modifica la base de datos, recetas, artículos ni menús existentes.

## Caso oficial
- Archivo: `Escandallos Boronat.xlsx`
- Hoja: `MENU BODA 31-1`
- Resultado esperado: 12 platos, 1 artículo directo y 1 complemento.

## Validación
- Tests unitarios específicos de clasificación, economía y seguridad.
- Prueba real contra el Excel oficial.
- Suite de regresión del proyecto.
