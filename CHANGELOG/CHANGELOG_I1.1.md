# I1.1 — Detector de escandallos antiguos

## Objetivo
Detectar de forma no destructiva múltiples fichas técnicas dentro de hojas Excel legacy como `MP boda 31-1`.

## Incluye
- Detección de bloques delimitados por `FICHA TÉCNICA`.
- Nombre de receta/elaboración desde marcadores `ARTÍCULO`, `ELABORACIÓN` o `RECETA`.
- Tipo, rendimiento, unidad, coste total y coste por ración/unidad.
- Detección de la tabla de ingredientes y extracción de cantidades, precios y costes.
- Comparación entre coste declarado y suma de ingredientes.
- Avisos de precios anómalos, cantidades ausentes, bloques incompletos y diferencias de coste.
- Informe JSON junto al Excel analizado.
- Nueva opción 9 en `Excel / importaciones`.

## Seguridad
I1.1 es **solo análisis**. No crea artículos, no importa recetas y no modifica la base de datos.

## Próximo sprint
I1.2 usará esta salida para hacer vista previa, resolver coincidencias con artículos y pedir confirmación antes de importar.
