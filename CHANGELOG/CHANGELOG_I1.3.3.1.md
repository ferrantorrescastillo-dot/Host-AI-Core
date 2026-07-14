# CHANGELOG I1.3.3.1 — Resolución de bloqueos de preimportación

## Añadido
- Nueva opción 17 en Excel / Importaciones.
- Resolución interactiva de cada bloqueo de preimportación.
- Creación controlada de recetas con nombre, rendimiento y al menos un ingrediente real.
- Vinculación con recetas existentes.
- Búsqueda de artículos por nombre para completar la receta.
- Recalculo automático de I1.3.3 tras cada resolución.
- Cambio de estado `BLOQUEADA` a `LISTA` cuando desaparecen todos los bloqueos.
- Copia de seguridad previa y escritura atómica de `escandallos.json`.
- Transformación del aprendizaje previo en vínculo definitivo conservando historial.

## Seguridad
- No importa menús.
- No permite crear recetas vacías.
- No duplica recetas activas con el mismo nombre.
- Mantener pendiente conserva el bloqueo.
- La importación definitiva sigue reservada para I1.3.4.
