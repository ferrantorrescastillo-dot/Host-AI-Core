# CHANGELOG I1.3.4.2 — Motor de escritura segura

- Motor transaccional con lista blanca de rutas.
- Backup completo previo a la escritura.
- Escritura JSON atómica mediante fichero temporal y `os.replace`.
- Verificación de JSON y huellas.
- Commit explícito.
- Rollback y restauración automática ante fallo.
- Auditoría JSONL por transacción.
- Diagnóstico aislado; la importación real de menús permanece deshabilitada.
