# RR1.6.1-A — Contexto global y Costes

## Objetivo
Corregir la pérdida de contexto detectada durante RR1.6 y asegurar que Eventos, Producción, Compras, Escandallos, Costes e IA reutilizan los mismos elementos activos.

## Cambios
- Nuevo contexto persistente en `SERVICIOS/contexto_global_rr161a.py`.
- Persistencia de evento, plan, necesidad, pedido y receta activos.
- Recuperación automática después de cambiar de módulo o reiniciar Host AI.
- La consola ya no inicializa esos identificadores a `None` en cada arranque.
- Costes reutiliza el evento activo persistido.
- Validación del evento guardado antes de calcular costes o rentabilidad.
- Mensaje más útil cuando el evento guardado ya no existe.
- Contexto del evento visible en el menú principal.
- IA RR1.5 recibe el evento persistido como contexto.
- El contador de Costes incluye precios explícitos y precios válidos incluidos en escandallos.

## Incidencias corregidas
- RR1.6-E001: pérdida del evento activo entre módulos.
- RR1.6-CO014: Costes no reconoce el evento seleccionado.
- Contador `Precios registrados: 0` pese a existir precios en escandallos.

## Validación
- 94 pruebas superadas.
- 0 fallos.
- Persistencia probada tras recrear la consola.
- Compatibilidad validada con todos los sprints anteriores.
