# Host AI 4.4.13 - Logs del proyecto

## Objetivo

Registrar ejecuciones importantes del proyecto para saber qué se ha lanzado, cuándo, cuánto ha tardado y si ha fallado.

Cada ejecución guarda:

- fecha
- módulo
- acción
- duración
- errores
- usuario
- restaurante
- detalle técnico

## Archivos

- `SERVICIOS/registro_logs_proyecto_4413.py`
- `APP/logs_proyecto_4413.py`
- `TESTS/test_4413_logs_proyecto.py`

## Archivo generado

```text
LOGS/host_ai_ejecuciones.jsonl
```

Es formato JSON Lines: una ejecución por línea.

## Uso manual

Ver resumen de logs:

```powershell
python APP/logs_proyecto_4413.py
```

## Integración con tests

El runner de tests 4.4.12 ya registra automáticamente una entrada cada vez que ejecuta un bloque de pruebas.
