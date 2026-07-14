# Host AI 5.2 — Datos mínimos y preguntas inteligentes

## Objetivo

Evitar que Host AI invente datos cuando el usuario pide organizar eventos, bodas o caterings sin haber cerrado información básica.

## Qué añade

- Gestor de datos mínimos para eventos.
- Preguntas inteligentes paso a paso.
- Integración con el orquestador 5.1.
- Bootloader actualizado para abrir el chat 5.2 desde la opción 1.

## Datos mínimos de evento

- Personas.
- Fecha.
- Hora del servicio.
- Tipo de menú.
- Lugar.
- Restricciones alimentarias.
- Objetivo: producción, compras, rentabilidad o flujo completo.

## Comportamiento esperado

Usuario:

> Tengo una boda para 180 personas el sábado.

Host AI:

> Perfecto. Antes de organizar el evento necesito cerrar unos datos mínimos para no inventar nada.
> ¿A qué hora es el servicio?

Cuando todos los datos están completos, Host AI permite pasar al flujo operativo de producción, stock, compras y rentabilidad.

## Prueba

```powershell
python -m TESTS.test_52_datos_minimos_evento
python main.py
```
