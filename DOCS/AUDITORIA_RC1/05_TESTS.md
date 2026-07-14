# RC1.1.5 — Auditoría TESTS

## Carpeta revisada

`TESTS/`

## Estado

Muy buena base, pero necesita organización.

El proyecto ya tiene muchos tests individuales y combinados. Esto es uno de los puntos fuertes de Host AI.

## Lo que está bien

- Hay tests para casi todos los módulos importantes.
- Existen tests combinados por bloque.
- Existe un test global Stable Candidate.
- Los tests han permitido validar compras, stock, producción, escandallos e IA conversacional.

## Tests críticos actuales

- `test_host_ai_3_0_stable.py`
- `test_inteligencia_compras_3041_3042_3043_3044_3045_3046_3047_3048.py`
- `test_gestion_inteligente_stock_3051_3052_3053_3054_3055_3056_3057_3058.py`
- `test_produccion_3061_3062_3063_3064_3065_3066_3067_3068.py`
- `test_escandallos_inteligentes_3071_3072_3073_3074_3075_3076_3077_3078.py`
- `test_ia_conversacional_3081_3082_3083_3084_3085_3086_3087_3088.py`

## Riesgos

- Hay demasiados tests sueltos sin clasificación.
- Algunos tests pueden ser demasiado simples.
- Algunos tests podrían ser interactivos o demo.
- `test_app_base_ejecutable.py` debería revisarse porque puede no ser apto para batería automática.

## Recomendaciones RC1

1. Clasificar tests en críticos, secundarios, manuales y legacy.
2. Mantener `test_host_ai_3_0_stable.py` como semáforo principal.
3. Crear un lanzador tipo `run_tests.py`.
4. Evitar tests interactivos dentro de la batería automática.
5. Añadir casos de error reales: datos vacíos, stock negativo, artículo inexistente, proveedor duplicado, receta incompleta.

## Prioridad

Alta.
