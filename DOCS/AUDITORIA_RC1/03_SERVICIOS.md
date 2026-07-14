# RC1.1.3 — Auditoría SERVICIOS

## Carpeta revisada

`SERVICIOS/`

## Estado

Funcionales y bien separados, pero necesitan catálogo y normalización.

`SERVICIOS` contiene la lógica real de negocio de Host AI. Es una de las carpetas más importantes del proyecto.

## Lo que está bien

- Buena separación por dominio.
- Servicios repartidos en compras, stock, producción, escandallos, IA conversacional, facturas, OCR, Excel e importaciones.
- No se recomienda mezclar la lógica de servicios dentro de pipelines ni Core.
- Los servicios parecen estar centrados en lógica de negocio, que es lo correcto.

## Riesgos

- Algunos servicios son largos y pueden crecer demasiado.
- Hay servicios antiguos y nuevos conviviendo.
- Falta una tabla clara que indique qué servicio usa cada pipeline y qué test lo valida.
- Falta una capa común de utilidades para servicios: validación, logs, errores y medición de tiempo.

## Recomendaciones RC1

1. Crear catálogo de servicios.
2. Clasificar servicios: core, producción, soporte, legacy, demo.
3. No refactorizar servicios grandes hasta tener tests claros.
4. Añadir progresivamente una capa común de logging y errores.

## Documento recomendado

`DOCS/CATALOGO_SERVICIOS_HOST_AI.md`

Campos recomendados:

- Servicio.
- Bloque.
- Pipeline asociado.
- Test asociado.
- Estado.
- Notas.

## Prioridad

Alta para RC1.
