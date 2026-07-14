# RC3.2 — Rendimiento para Piloto

## Objetivo

Añadir una capa ligera para medir tiempos de ejecución antes de llevar Host AI a pruebas reales con restaurantes.

## Archivos añadidos

```text
SERVICIOS/medidor_rendimiento_piloto.py
TESTS/test_rc3_2_rendimiento_piloto.py
DOCS/RC3_2_RENDIMIENTO_PILOTO.md
```

## Qué mide

- Tiempo de ejecución en milisegundos.
- Estado de la operación:
  - `ok`
  - `aviso`
  - `lento`
  - `error`
- Resumen acumulado de mediciones.

## Qué NO hace

- No modifica motores existentes.
- No cambia lógica de negocio.
- No escribe datos.
- No sustituye a un profiler avanzado.

## Comando de prueba

```powershell
python TESTS\test_rc3_2_rendimiento_piloto.py
python TESTS\test_host_ai_3_0_stable.py
```

## Criterio de aceptación

El test debe mostrar:

```text
TEST OK - Host AI RC3.2 Rendimiento para Piloto
```
