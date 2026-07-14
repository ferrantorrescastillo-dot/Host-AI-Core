# Host AI 4.5.7 - Auditoría completa del sistema

Este sprint añade un registro centralizado de acciones importantes.

## Registra

- usuario
- restaurante
- módulo
- acción
- entidad afectada
- valores antes/después
- errores
- fecha y hora

## Uso

```powershell
python APP/auditoria_sistema_457.py
python TESTS/test_457_auditoria_sistema.py
```

El servicio principal es `SERVICIOS/auditoria_sistema_457.py`.
