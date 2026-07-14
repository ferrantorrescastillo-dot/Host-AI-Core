# I1.3.4.1.2 — Clasificador gastronómico inteligente

## Objetivo
Clasificar cada línea del menú antes de activar reconocimiento y árbol semántico. La simulación debe distinguir entre platos/recetas y elementos que pertenecen a bodega, complementos o catálogo comercial.

## Tipos iniciales
- PLATO_RECETA
- PLATO_COMPUESTO
- PLATO_PENDIENTE
- APERITIVO_PREPARADO (A.P)
- MATERIA_PRIMA (M.P)
- ARTICULO_COMERCIAL
- BEBIDA
- VINO
- CAVA
- AGUA
- CAFE_INFUSION
- PAN
- COMPLEMENTO
- SERVICIO
- ELEMENTO_PENDIENTE

## Precedencia
1. Una receta completa catalogada prevalece sobre palabras internas como pan, agua o salsa.
2. Los prefijos A.P y M.P se interpretan según la regla oficial de Host AI.
3. Bebidas, vinos, cavas, aguas, cafés y panes no activan el árbol semántico.
4. Artículos catalogados sin receta completa se importan como artículos directos o aperitivos preparados.
5. Solo platos y componentes culinarios pendientes llegan al árbol semántico y al MUR.

## Limpieza semántica
Se excluyen como ruido de componentes expresiones comerciales o contextuales como:
- POR PAX
- PRECIO PAX
- PRECIO KG
- MENU CALÇOTADA
- MENU BBQ
- envases, unidades y notas comerciales

## Integridad
El sprint sigue siendo una simulación. No existe ejecución del plan ni escritura en datos de negocio. Se conservan las huellas SHA-256 de los ficheros críticos.

## Idempotencia del plan
Los identificadores de acciones incluyen versión, índice y menu_id para evitar colisiones cuando varias hojas comparten el mismo título interno.
