# PILOTO-1 — Recepción inteligente de mercancía

## Añadido
- Flujo único para PDF con texto, Excel, CSV, TXT, JSON e imágenes mediante texto OCR/manual.
- Vista previa obligatoria sin escrituras.
- Búsqueda por nombre; proveedor como segunda vía.
- Bandeja de líneas exactas, probables y sin resolver.
- Vinculación, alta controlada u omisión por línea.
- Confirmación explícita `RECEPCIONAR`.
- Transacción con backup, escritura atómica y rollback.
- Actualización de artículos, precios, lotes, movimientos, proveedores e histórico de facturas.
- Idempotencia por SHA-256 del documento.
- Diagnóstico aislado accesible desde Modo Piloto → Recepción → opción 9.

## Límites
- Las imágenes requieren texto OCR/manual si el OCR local no ofrece contenido fiable.
- No se recalculan todavía todos los escandallos afectados; se registra la variación de precio para el siguiente bloque del piloto.
