# CHANGELOG I1.3.4.3b — Corrección de relaciones de componentes

## Correcciones
- Los componentes ya no dependen exclusivamente del nombre textual del plato.
- Construcción en dos pasadas: primero menús/secciones/platos; después componentes y relaciones.
- Soporte de `plato_id`, `plato_accion_id` y alias de nombres originales o renombrados.
- Compatibilidad conservadora con sesiones antiguas sin identificador de plato.
- Bloqueo explícito si el destino es ambiguo.
- Identificador estable `componente_id` y protección contra relaciones duplicadas.
- Mensajes de error enriquecidos con menú y referencias de plato.

## Caso corregido
- `Salsa naranja` y `Parmentier de patata` quedan vinculados al plato
  `Solomillo de cerdo con parmentier patata i salsa naranja`.

## Seguridad
- La construcción completa del catálogo ocurre antes de iniciar la transacción.
- Si falta o es ambiguo el plato destino, no se escribe ningún dato.
