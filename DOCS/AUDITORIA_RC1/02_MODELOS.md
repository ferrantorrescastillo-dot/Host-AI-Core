# RC1.1.2 — Auditoría MODELOS

## Carpeta revisada

`MODELOS/`

## Estado

Bien estructurada y usable.

La carpeta contiene modelos separados por dominio y utiliza principalmente `dataclass`, lo cual es correcto para estructuras de datos.

## Lo que está bien

- Buena separación por dominio: compras, stock, producción, escandallos, importación, OCR, facturas e IA conversacional.
- Uso correcto de modelos como estructuras de datos.
- `SolicitudPipeline` y `ResultadoPipeline` son una buena base arquitectónica.
- Los nombres de modelos recientes son bastante claros y coherentes.

## Riesgos

- Existen modelos legacy y modelos nuevos conviviendo.
- Puede haber nombres de clases repetidos en archivos diferentes.
- Algunos modelos empiezan a crecer demasiado y podrían dividirse en subdominios.

## Recomendaciones RC1

1. Crear catálogo de modelos por bloque.
2. Marcar modelos antiguos como legacy si ya no son principales.
3. Evitar nombres de clases duplicados.
4. Mantener los modelos sin lógica de negocio pesada.

## Documento recomendado

`DOCS/ARQUITECTURA_MODELOS.md`

## Prioridad

Media.
