# I1.3.4.4.2 — Corrección inteligente masiva y navegación por incidencias

## Incorporado
- Resolución automática conservadora de casos unívocos.
- Vinculación automática solo con coincidencia exacta y única.
- Creación/asignación automática de secciones inequívocas.
- Recalculo económico masivo.
- Filtros: todas, errores, avisos, código y menú.
- Agrupación por tipo de incidencia y por menú.
- Acciones masivas por grupo.
- Conservación de incidencias ambiguas para revisión manual.
- Vista previa sin modificar datos reales hasta `GUARDAR`.
- Nueva opción de consola 33.

## Seguridad
- No inventa recetas ni artículos.
- No selecciona entre varios candidatos.
- No escribe `DATOS/db/menus.json` antes de confirmación explícita.
- Reutiliza backup, escritura atómica, rollback y reauditoría de I1.3.4.4.1.
