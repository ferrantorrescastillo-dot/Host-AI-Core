# Host AI 4.5.1–4.5.2 - Corrección SQLite Windows

## Problema corregido
En Windows, SQLite deja el archivo `host_ai.db` bloqueado si la conexión no se cierra explícitamente.

El contexto nativo de `sqlite3.Connection` hace commit/rollback, pero no cierra siempre el descriptor del archivo de forma inmediata.

## Solución
Se añade el contexto `conexion()` en `GestorBaseDatosDefinitiva451`:

- abre conexión
- activa foreign keys
- hace commit si todo va bien
- hace rollback si hay error
- cierra siempre con `con.close()`

`GestorMultiRestaurante452` queda actualizado para usar este contexto.

## Validación
Ejecutar:

```powershell
python TESTS/test_451_base_datos_definitiva.py
python TESTS/test_452_multi_restaurante.py
```
