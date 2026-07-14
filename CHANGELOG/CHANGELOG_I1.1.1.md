# I1.1.1 — Detector Multi-Escandallos

## Correcciones

- Detecta cada fila `ARTÍCULO | nombre` como inicio independiente de receta.
- Ya no depende de que `FICHA TÉCNICA` se repita antes de cada bloque.
- No confunde la cabecera `ARTICULO | KG | €/UN...` con una receta.
- Cierra cada bloque al encontrar el siguiente inicio de receta.
- Lee valores cacheados de fórmulas mediante una segunda apertura `data_only=True`.
- Detecta mejor coste total, coste unitario y rendimiento.
- Mantiene la suma calculada de ingredientes como referencia cuando falta el coste declarado.
- Conserva el modo seguro: solo analiza y genera JSON; no importa datos.

## Compatibilidad

Compatible con I1.2 e I1.3. Sustituye únicamente el detector de I1.1.

## Pruebas

- 4 pruebas específicas del detector.
- 6 pruebas superadas junto con la importación segura I1.2.
