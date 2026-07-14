# I1.3.4.1 — Simulación de importación de menús

## Objetivo
Convertir la preimportación certificada I1.3.3 en un plan determinista de cambios sin escribir datos de negocio.

## Acciones planificadas
- Crear o actualizar el menú.
- Crear o reutilizar secciones.
- Crear relaciones menú-plato.
- Vincular recetas, salsas, guarniciones y artículos directos.
- Registrar complementos y datos económicos.
- Marcar como bloqueada cualquier acción que dependa de una entidad no resuelta.

## Seguridad
- No existe confirmación de importación.
- `escrituras_habilitadas=False`.
- Se calculan huellas SHA-256 antes y después sobre catálogos y colecciones críticas.
- Si cambia un archivo vigilado, el resultado pasa a `ERROR_INTEGRIDAD`.
- Los identificadores de plan y acciones son deterministas para facilitar idempotencia en I1.3.4.2.
