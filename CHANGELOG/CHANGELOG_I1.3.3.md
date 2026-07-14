# CHANGELOG I1.3.3 — Preimportación definitiva de menús

## Añadido
- Contrato final de preimportación de menús.
- Consolidación de menú, secciones, platos, componentes, artículos directos, complementos y datos económicos.
- Motor de bloqueos previo a cualquier escritura.
- Bloqueo específico para propuestas de receta todavía no creadas.
- Explicación de acciones necesarias para desbloquear la futura importación.
- Opción 16 en Excel / Importaciones.

## Seguridad
- No importa menús.
- No crea recetas ni artículos.
- No modifica relaciones ni catálogos.
- Mantiene `importacion_disponible = False` incluso cuando la preimportación está lista.
