# CHANGELOG I1.3.4.1.1 — Detección y simulación multimenú

## Añadido
- Detector multihoja que combina nombre de hoja y validación por contenido.
- Clasificación `MENU_CONFIRMADO`, `MENU_PROBABLE` y `NO_MENU`.
- Exclusión expresa de hojas M.P/MP, fichas técnicas, plantillas, listados y hojas vacías.
- Reconocimiento de menús aunque la hoja no empiece por MENU, como una hoja de comunión con estructura interna válida.
- Selección interactiva de todos los menús o un subconjunto por número.
- Resumen separado entre menús detectados en el Excel, menús existentes en Host AI y menús a crear/actualizar.
- Simulación conjunta de varios menús con integridad SHA-256 y cero escrituras.

## Compatibilidad
- Mantiene intacto I1.3.4.1 y toda la línea certificada anterior.
- La importación definitiva continúa deshabilitada.
