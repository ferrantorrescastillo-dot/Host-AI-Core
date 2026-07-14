# Host AI 5.4.11 — Continuador Inteligente del Flujo

Cuando existe un flujo activo, `seleccionar` abre las acciones pendientes y la respuesta siguiente puede ser un número o el nombre de la acción.
No se vuelve al clasificador general.

## Prueba real
1. Crea el evento hasta llegar a la confirmación.
2. Escribe `sí`.
3. Escribe `seleccionar`.
4. Escribe `1`, `2` o `3`.

## Pruebas técnicas
```bash
python TESTS/test_5411_continuador_flujo.py
python APP/continuador_flujo_5411.py
```
