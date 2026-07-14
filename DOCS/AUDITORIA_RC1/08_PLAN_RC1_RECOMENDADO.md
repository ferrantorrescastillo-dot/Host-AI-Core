# Plan recomendado para Host AI 3.0 RC1

## Objetivo

Convertir Host AI 3.0 Stable Candidate en una versión RC1 lista para una primera prueba controlada con restaurantes.

## Regla principal

No añadir funcionalidades nuevas hasta terminar RC1.

## Tareas recomendadas

### RC1-A — Limpieza de estructura

- Eliminar copias internas duplicadas del proyecto.
- Eliminar `__pycache__`.
- Revisar que solo exista una carpeta raíz válida.

### RC1-B — Tests

- Mantener `test_host_ai_3_0_stable.py` como test principal.
- Clasificar tests.
- Revisar `test_app_base_ejecutable.py`.
- Crear lanzador de tests.

### RC1-C — Documentación central

- Manual técnico.
- Guía de instalación piloto.
- Checklist de piloto.
- Catálogo de servicios.
- Catálogo de pipelines.
- Catálogo de tests.

### RC1-D — Core y Orquestador

- No refactorizar fuerte todavía.
- Documentar registro de pipelines.
- Separar progresivamente por bloques si es necesario.

### RC1-E — Datos para piloto

- Preparar dataset mínimo de restaurante.
- Definir artículos mínimos.
- Definir recetas mínimas.
- Definir proveedores mínimos.
- Definir stock inicial.

## Criterio de salida a piloto

Host AI puede pasar a piloto cuando:

1. `test_host_ai_3_0_stable.py` pase.
2. Exista guía de instalación.
3. Exista checklist de piloto.
4. Sepamos qué datos mínimos cargar.
5. El usuario pueda ejecutar el flujo principal sin tocar código.

## Próximo paso recomendado

RC1-A: limpieza de estructura y eliminación de duplicados/copias internas.
