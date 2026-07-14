# RC3.3 — Logs para Piloto

## Objetivo

Añadir una capa simple de logs para pruebas reales en restaurante.

## Archivos añadidos

```text
SERVICIOS/logger_piloto_host_ai.py
TESTS/test_rc3_3_logs_piloto.py
DOCS/RC3_3_LOGS_PILOTO.md
LOGS/
```

## Qué registra

- Acciones importantes.
- Avisos.
- Errores controlados.
- Eventos críticos.
- Datos complementarios en formato JSON.

## Niveles

```text
INFO
AVISO
ERROR
CRITICO
```

## Comandos de prueba

```powershell
python TESTS\test_rc3_3_logs_piloto.py
python TESTS\test_host_ai_3_0_stable.py
```

## Criterio de aceptación

Debe aparecer:

```text
TEST OK - Host AI RC3.3 Logs para Piloto
```
