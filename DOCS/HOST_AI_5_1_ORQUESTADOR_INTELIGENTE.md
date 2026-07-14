# Host AI 5.1 — Orquestador Inteligente

## Objetivo

Convertir el Núcleo IA en un coordinador de flujos, no solo en un clasificador de intenciones.

El orquestador analiza una petición natural y decide qué módulos deben intervenir y en qué orden.

Ejemplo:

> Tengo una boda para 180 personas el sábado y dime qué tengo que comprar.

Host AI prepara un flujo:

1. Evento 4.7
2. Producción 4.6
3. Stock 4.3
4. Compras 4.5/4.8
5. Rentabilidad 4.8
6. Respuesta unificada 5.1

## Seguridad

El 5.1 no modifica datos directamente salvo cuando delega en el flujo seguro de recepción 5.0.5 y el usuario confirma.

## Archivos

- `SERVICIOS/orquestador_inteligente_51.py`
- `APP/orquestador_inteligente_51.py`
- `TESTS/test_51_orquestador_inteligente.py`
- `DOCS/HOST_AI_5_1_ORQUESTADOR_INTELIGENTE.md`

## Prueba

```powershell
python -m TESTS.test_51_orquestador_inteligente
python -m APP.orquestador_inteligente_51
```

## Siguiente paso recomendado

5.2 debería empezar a ejecutar algunos de esos pasos reales con confirmación, especialmente:

- evento → producción → stock → compras;
- producción → stock → compras;
- rentabilidad → recomendaciones.
