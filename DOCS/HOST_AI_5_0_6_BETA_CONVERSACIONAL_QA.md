# HOST AI 5.0.6 — Beta Conversacional QA

Este bloque crea la primera batería profesional de pruebas conversacionales de Host AI.

## Objetivo

Medir si Host AI entiende conversaciones reales de cocina antes de ejecutar motores.

## Incluye

- `QA/BETA_1_100_CONVERSACIONES.json`
- Casos organizados por categoría:
  - Recepción
  - Compras
  - Producción
  - Eventos
  - Stock
  - Rentabilidad
  - General
- Servicio ejecutor `SERVICIOS/beta_conversacional_qa_506.py`
- APP `APP/beta_conversacional_qa_506.py`
- Test `TESTS/test_506_beta_conversacional_qa.py`

## Uso

```powershell
python -m TESTS.test_506_beta_conversacional_qa
python -m APP.beta_conversacional_qa_506
```

También aparece como opción en el bootloader.

## Criterio de puntuación

- OK: intención correcta y confianza suficiente.
- PARCIAL: intención correcta con confianza baja.
- FAIL: intención incorrecta.

## Objetivo de calidad

- Beta 1: 70%
- Beta 2: 85%
- Release Candidate: 95%
