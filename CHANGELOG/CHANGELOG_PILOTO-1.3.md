# PILOTO-1.3 — Producción guiada

## Objetivo
Convertir el motor de ejecución de producción ya existente en un flujo diario comprensible para cocina, sin duplicar su lógica ni modificar todavía el stock.

## Cambios
- Nueva capa `ProduccionGuiadaPiloto13` sobre `core.produccion_real`.
- Nueva consola centrada en la pregunta «¿Qué acaba de pasar?».
- Selección humana de la siguiente acción: resolver bloqueo, continuar, reanudar, iniciar o cerrar.
- Estados, prioridades y tiempos expresados en lenguaje operativo.
- Acciones guiadas: iniciar, pausar, reanudar, finalizar, avance, incidencia y resolución de bloqueo.
- Acceso conservado a la gestión avanzada de producción.
- La opción Producción del modo piloto abre ahora Producción guiada.

## Fuera de alcance
- No descuenta stock. Eso corresponde a PILOTO-1.4.
- No sustituye ni reescribe el motor de producción real.
