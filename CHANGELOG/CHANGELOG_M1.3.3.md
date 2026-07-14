# CHANGELOG M1.3.3 — Validación culinaria inteligente

## Añadido
- Validador explicable de borradores de receta.
- Estados `VALIDADA`, `REVISAR` y `BLOQUEADA`.
- Hallazgos con código, severidad, categoría, evidencia y recomendación.
- Validación de nombre, rendimiento, ingredientes, cantidades, unidades y vínculos.
- Detección de ingredientes duplicados.
- Regla oficial `M.P = MATERIA_PRIMA` y `A.P = APERITIVO`.
- Bloqueo de un `A.P` usado como materia prima automática.
- Avisos de coherencia culinaria para unidades sospechosas.
- Cálculo de coste conocido total y por ración.
- Aviso de coste incompleto cuando falta precio.
- Revisión de elaboración, tiempos, conservación y alérgenos.
- Diagnóstico aislado accesible desde Excel / Importaciones, opción 23.

## Seguridad
- No crea recetas.
- No modifica artículos.
- No modifica catálogos reales.
- Las sospechas culinarias no se convierten en errores sin evidencia crítica.
- Los artículos sin precio generan aviso económico, no invalidación automática.

## Pruebas
- 8/8 tests específicos M1.3.3.
- 82/82 tests de regresión I1.3 + M1.1–M1.3.3.
