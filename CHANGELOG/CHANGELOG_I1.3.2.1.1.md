# CHANGELOG I1.3.2.1.1 — Corrección del catálogo de reconocimiento

## Correcciones
- El motor carga ahora recetas desde `DATOS/db/escandallos.json` y `DATOS/db/escandallos_canonicos.json`.
- Se eliminan duplicados por nombre normalizado y se priorizan las recetas operativas/importadas.
- Una receta tiene prioridad sobre un artículo histórico con el mismo nombre del plato.
- Se añade reconocimiento equivalente completo para variaciones mínimas reales (`y/i`, `de`, `porc`, `boda`).
- Los platos compuestos no se convierten indebidamente en receta completa.
- Un artículo exacto aislado se muestra como `ARTICULO_COMPLETO`, no como `MAPA_PARCIAL`.
- Se actualiza la opción de consola a I1.3.2.1.1.

## Sin cambios
- No se importan menús.
- No se asignan roles semánticos.
- No se modifica ninguna base de datos.
- I1.3.1 y el importador legacy permanecen intactos.
