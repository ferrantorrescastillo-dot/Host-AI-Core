# HOST AI 5.5.6E.3.3

## Flujo conversacional inteligente de planificación

- Mantiene la receta activa después de guardar la ficha de producción.
- Interpreta `sí`, `adelante`, `continúa`, `planifica` y `hazlo` dentro del flujo activo.
- Solicita el objetivo cuando falta: personas, raciones o unidades.
- Acepta el número de cocineros en la misma frase.
- Genera el planning real desde la ficha validada.
- Limpia nombres de fases como `Cocer las patatas durante` a `Cocer patatas`.
- Evita enviar respuestas cortas al clasificador de conversación general.

## Prueba

```powershell
python TESTS/test_556e33_flujo_post_ficha.py
```

## Conversación esperada

1. Registrar y confirmar una ficha.
2. Responder `sí`.
3. Responder `150 personas con 3 cocineros`.
4. Host AI genera el planning real.
