# Host AI 3.0.6.7 + 3.0.6.8 - Producción

Este paquete cierra el bloque Host AI 3.0.6 Producción con dos módulos:

## 3.0.6.7 Optimizador Inteligente de Producción
Optimiza el plan operativo a partir de planificación, asignación, control y replanificación.

Analiza:
- tiempos pasivos aprovechables,
- huecos por recurso,
- agrupación de tareas compatibles,
- carga por cocinero,
- retrasos y acciones de replanificación.

## 3.0.6.8 Cierre Inteligente de Producción
Valida que el bloque 3.0.6 funcione como sistema completo.

Comprueba:
- análisis,
- alertas,
- planificación,
- asignación,
- control,
- replanificación,
- optimización,
- coherencia global.

## Pruebas
```bash
python TESTS\test_optimizador_inteligente_produccion.py
python TESTS\test_cierre_inteligente_produccion.py
python TESTS\test_produccion_3061_3062_3063_3064_3065_3066_3067_3068.py
```
