# Arquitectura técnica I1.3.4.1.1

## Objetivo
Detectar de forma fiable todas las hojas de menú de un libro Excel y permitir simular una, varias o todas.

## Estrategia de detección
1. Pistas positivas del nombre: MENU/MENÚ, boda, comunión, calçotada, BBQ, fin de año, agencia.
2. Validación interna: encabezado de menú, secciones gastronómicas, PVP/neto/coste/food cost y líneas con coste.
3. Exclusiones: M.P/MP, ficha técnica de plato, plantilla, listado de artículos y hoja vacía.
4. Clasificación por puntuación: confirmado, probable o no menú.

El nombre de la hoja es una pista fuerte, nunca la única fuente de verdad.

## Seguridad
La simulación reutiliza la preimportación certificada, genera acciones deterministas y compara huellas SHA-256 antes y después. Cualquier modificación produce `ERROR_INTEGRIDAD`.
