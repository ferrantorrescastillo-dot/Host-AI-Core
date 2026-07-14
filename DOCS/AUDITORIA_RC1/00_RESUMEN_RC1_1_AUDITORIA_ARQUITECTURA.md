# Host AI RC1.1 — Auditoría de Arquitectura

## Objetivo

Preparar Host AI 3.0 para una versión RC1 estable antes de empezar pruebas controladas con restaurantes.

Esta auditoría no añade funcionalidades nuevas. Su objetivo es revisar la arquitectura actual, detectar riesgos, ordenar prioridades y decidir qué limpiar antes de usar Host AI en un entorno real.

## Estado actual

Host AI 3.0 tiene una base funcional amplia:

- Importación inteligente.
- Inteligencia de compras.
- Gestión inteligente del stock.
- Producción.
- Escandallos inteligentes.
- IA conversacional.
- Test global Stable Candidate.

El test global `TESTS/test_host_ai_3_0_stable.py` valida los bloques principales.

## Conclusión general

Host AI ya tiene suficiente funcionalidad para empezar una fase de estabilización. No se recomienda añadir más módulos antes de RC1.

La prioridad ahora es:

1. Limpiar estructura.
2. Documentar arquitectura.
3. Clasificar tests.
4. Revisar cierres críticos.
5. Preparar piloto real.

## Riesgos principales detectados

- Proyecto duplicado dentro del propio ZIP/carpeta.
- Core demasiado centralizado.
- Orquestador creciendo demasiado.
- Falta de catálogos de servicios, pipelines y tests.
- Algunos tests pueden ser interactivos o no aptos para ejecución automática.
- Documentación muy distribuida por sprints, pero falta documentación central de producto.

## Próximo objetivo recomendado

Crear Host AI 3.0 RC1 con:

- Test global oficial.
- Documentación central.
- Checklist de instalación.
- Checklist de piloto.
- Limpieza de archivos duplicados y `__pycache__`.
- Clasificación de tests críticos/secundarios/manuales.
