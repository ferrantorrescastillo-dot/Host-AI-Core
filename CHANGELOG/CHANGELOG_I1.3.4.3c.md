# I1.3.4.3c — Identidad definitiva de platos y componentes

## Correcciones
- Deduplicación de varias acciones `PLATO_MENU` que representan el mismo plato lógico.
- Identidad canónica por `plato_id`, acción padre y alias original/renombrado.
- Propagación de un único `plato_id` a receta principal, salsa, guarnición, elaboración, condimento y acabado.
- Deduplicación de candidatos por identidad, no por objeto o texto.
- Compatibilidad con sesiones antiguas que no contienen `plato_id`.
- Bloqueo explícito cuando dos identidades realmente distintas entran en contradicción.
- Idempotencia de platos y componentes.

## Caso corregido
`Salsa naranja` y `Parmentier de patata` se vinculan al mismo plato padre:
`Solomillo de cerdo con parmentier patata i salsa naranja`.

## Seguridad
La estructura se valida antes de iniciar la transacción. Una contradicción de identidad no escribe datos reales.
