# CHANGELOG I1.3.4.1.2

## Añadido
- Clasificador gastronómico previo al árbol semántico.
- Tipos específicos para bebidas, vino, cava, agua, café, pan, A.P, M.P, artículos comerciales, complementos y servicios.
- Relación `BEBIDA_MENU` separada de `PLATO_MENU`.
- Filtrado de ruido comercial y contextual.
- Deduplicación de secciones y entidades por menú.
- Identificadores de acción únicos incluso con títulos de menú repetidos.
- Opción 25 en Excel / Importaciones.

## Corregido
- Bebidas y vinos ya no se tratan como platos.
- `Caña de cerveza` no se divide en componentes.
- `MENU CALÇOTADA ... POR PAX` conserva la receta real y elimina contexto comercial.
- Secciones `POSTRES` repetidas se crean una sola vez por menú.
- Los A.P y M.P respetan su semántica oficial.

## Seguridad
- Cero escrituras en catálogos de negocio.
- Importación definitiva deshabilitada.
