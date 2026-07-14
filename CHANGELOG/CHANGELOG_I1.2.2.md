# I1.2.2 — Revisión y aprendizaje de vinculaciones

## Objetivo
Resolver manualmente únicamente los ingredientes ambiguos de I1.2.1 y recordar las decisiones para futuras importaciones.

## Cambios
- Revisión interactiva de vínculos `probable` y `sin_resolver`.
- Elección entre candidatos sugeridos.
- Búsqueda manual en el catálogo.
- Creación opcional de un artículo nuevo.
- Posibilidad de dejar un ingrediente pendiente.
- Memoria persistente en `DATOS/db/memoria_vinculaciones_i122.json`.
- Una decisión se aplica a todas las apariciones del mismo texto de ingrediente.
- En importaciones posteriores, los vínculos aprendidos se aplican como exactos.
- Se recalcula la vista previa después de cada revisión.
- La importación sigue bloqueando recetas con vínculos no resueltos.

## Seguridad
- La memoria solo se guarda tras una decisión explícita.
- La base de recetas no se modifica durante la revisión.
- La importación final sigue requiriendo confirmación.
