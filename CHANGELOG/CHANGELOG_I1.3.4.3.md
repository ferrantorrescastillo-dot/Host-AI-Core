# CHANGELOG I1.3.4.3 — Importación definitiva de menús

- Añadido importador definitivo conectado al motor de escritura segura I1.3.4.2.
- Persistencia real en `DATOS/db/menus.json` mediante backup, escritura atómica, commit y rollback.
- Creación y actualización idempotente por `menu_id` o nombre normalizado.
- Persistencia de secciones, platos, componentes, artículos directos, bebidas, complementos, servicios y datos económicos.
- Validación obligatoria de plan `LISTA_PARA_TRANSACCION`, sin bloqueos.
- Confirmación explícita escribiendo `IMPORTAR` antes de tocar datos reales.
- Diagnóstico aislado, repetición idempotente y auditoría.
