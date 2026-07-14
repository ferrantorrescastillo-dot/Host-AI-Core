# HOST AI 5.0.8 — Afinador Compras + Rentabilidad

## Objetivo
Corregir los fallos principales detectados por la Beta Conversacional 5.0.6 tras el refuerzo 5.0.7.

## Mejora principal
El clasificador `SERVICIOS/clasificador_intenciones_503.py` mantiene la misma clase e imports para no romper compatibilidad, pero sube a versión interna 5.0.8.

## Casos corregidos

### Compras
- `Prepara la compra de hoy.`
- `¿Qué falta comprar para el evento?`
- `Tengo que pedir tomate.`
- `Revisa si hay que comprar pescado.`
- `¿Cuánto tengo que pedir de arroz?`

### Rentabilidad
- `Simula subir la paella a 48 euros.`
- `Controla mermas de producción.`
- `Comparar coste entre proveedores.`
- `Informe financiero inteligente.`

## Prueba
```powershell
python -m TESTS.test_508_afinador_compras_rentabilidad
python -m APP.beta_conversacional_qa_506
```

## Resultado esperado
Subir la Beta Conversacional por encima de 85 puntos si los parches 5.0.1–5.0.7 ya están aplicados.
