# Certificación — PILOTO-1.3 Producción guiada

Estado: **CERTIFICADO**

## Verificaciones
- El servicio reutiliza `core.produccion_real`.
- No existe una segunda persistencia de planes o tareas.
- Las acciones se delegan al motor ya certificado.
- Los planes terminados o cancelados no aparecen como trabajo operativo.
- Los bloqueos tienen prioridad sobre el resto del trabajo.
- Una tarea en curso se recomienda antes de abrir otra.
- Las duraciones se muestran en horas y minutos.
- La gestión avanzada continúa accesible.
- No se realizan movimientos de stock.

## Regresión ejecutada
16 tests superados, incluyendo PILOTO-1.3, Mi Jornada, Bandeja de trabajo, ejecución básica y panel de producción.
