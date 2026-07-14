# CERTIFICACIÓN I1.3.4.3b

## Objetivo
Corregir el fallo `Componente sin plato destino: Salsa naranja` detectado en la primera importación real.

## Resultado
- Relaciones plato–componente por identidad estable: OK.
- Componentes procesados aunque aparezcan antes del plato en el plan: OK.
- Sesiones renombradas con `plato_id`: OK.
- Compatibilidad con sesiones antiguas mediante alias y coincidencia conservadora: OK.
- Ambigüedades: bloqueadas, nunca resueltas silenciosamente.
- Idempotencia de componentes: OK.
- Fallo de destino antes de cualquier escritura: OK.

## Tests
- Bloque específico e integración I1.3.4.x: **32/32 superados**.
- Suite global: mantiene 3 errores de colección preexistentes ajenos a este sprint.

## Datos reales
- Modificados durante certificación: **0**.
