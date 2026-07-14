# CHANGELOG M1.2 — Resolutor de artículos

## Añadido
- Resolutor real de artículos registrado mediante `IResolutorMUR`.
- Búsqueda prioritaria por nombre y filtro de proveedor como segunda vía.
- Vinculación con artículos existentes.
- Alta controlada mediante el servicio oficial `GestorArticulos416`.
- Unidad obligatoria como dato crítico.
- Detección de duplicados probables antes de crear.
- Política configurable para artículos sin precio.
- Estados de calidad `COMPLETA`, `PENDIENTE` y `BLOQUEADA`.
- Copias de seguridad previas a altas y ediciones.
- Aprendizaje sugerido para equivalencias confirmadas.
- Diagnóstico M1.2 aislado del catálogo real.

## Seguridad
- El diagnóstico trabaja sobre `DATOS/mur/diagnostico_m12_articulos.json`.
- No modifica el catálogo real durante la prueba.
- No altera recetas, menús, compras, stock ni proveedores.
