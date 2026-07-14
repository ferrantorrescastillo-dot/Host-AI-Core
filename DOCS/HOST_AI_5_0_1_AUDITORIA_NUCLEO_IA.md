# HOST AI 5.0.1 — Auditoría del Núcleo IA

## Objetivo

Este bloque no crea un nuevo motor. Audita el núcleo conversacional actual para detectar por qué algunas frases reales no activan módulos que ya existen.

Ejemplo detectado en prueba manual:

```text
Han llegado 25 kg de arroz bomba de Makro a 2,15 €/kg.
```

El módulo de recepción existe, pero el chat no lo enruta todavía.

## Archivos incluidos

- `APP/auditoria_nucleo_ia_501.py`
- `SERVICIOS/auditoria_nucleo_ia_501.py`
- `TESTS/test_501_auditoria_nucleo_ia.py`
- `DOCS/HOST_AI_5_0_1_AUDITORIA_NUCLEO_IA.md`

## Qué audita

- Recepción de mercancía por texto.
- Creación de evento.
- Necesidades de compra.
- Rentabilidad de platos.
- Planificación de producción con evento activo.

## Conclusión esperada

El cuello de botella está en `MOTORES/motor_asistente_conversacional.py`, concretamente en `detectar_intencion`.

La solución no es duplicar motores, sino ampliar las intenciones del chat para que pueda llamar a los módulos ya construidos en Host AI 4.x.

## Prueba

```powershell
python -m TESTS.test_501_auditoria_nucleo_ia
```

## Uso manual

```powershell
python APP/auditoria_nucleo_ia_501.py
```

## Siguiente sprint recomendado

**5.0.2 — Corrección de intenciones críticas del chat**

- Recepción: `han llegado`, `ha venido`, `me ha traído`, `albarán`, `factura`.
- Compras: `qué tengo que comprar`, `qué falta`, `pedido para mañana`.
- Rentabilidad: `beneficio`, `margen`, `plato que menos deja`.
- Producción con contexto: `organízame`, `planifica`, `qué hago hasta el servicio`.
