# CHANGELOG M1.1 — Núcleo del Motor Universal de Resolución

## Añadido
- Modelos universales de conflicto, checkpoint, sesión, resultado y auditoría.
- Enumeraciones de entidad, conflicto, severidad, estado y acción.
- Máquina de estados con validación estricta de transiciones.
- Registro dinámico de resolutores mediante `IResolutorMUR`.
- Orquestador MUR independiente de recetas, artículos y otros dominios.
- Repositorio intercambiable en memoria y persistencia JSON atómica.
- Checkpoints versionados para futura reanudación de flujos.
- Auditoría completa de detección, clasificación, resolución y cierre.
- Diagnóstico seguro desde Excel / Importaciones, opción 18.

## Seguridad
- No se han integrado resolutores reales.
- No se modifican recetas, artículos, menús, compras, stock ni producción.
- El diagnóstico escribe exclusivamente en `DATOS/mur/diagnostico_m11.json`.
- Un conflicto solo se cierra tras confirmar mediante recalculo que desapareció.

## Compatibilidad
- Toda la regresión I1.3 permanece operativa.
