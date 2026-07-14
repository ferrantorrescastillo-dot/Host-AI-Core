# RC1.1.4 — Auditoría PIPELINES

## Carpeta revisada

`PIPELINES/`

## Estado

Funcionales y alineados con la arquitectura.

Los pipelines reflejan correctamente la filosofía del proyecto: la IA o el usuario no ejecutan servicios directamente, sino que pasan por pipelines.

## Lo que está bien

- Arquitectura consolidada: solicitud, pipeline, servicio, resultado.
- Hay pipelines para los grandes bloques del sistema.
- Nomenclatura bastante clara.
- Buena separación entre pipeline y servicio.

## Riesgos

- Diferencias de estilo entre pipelines antiguos y nuevos.
- Falta un catálogo pipeline → servicio → test.
- Algunos pipelines podrían ser demos o pruebas y no deberían usarse en piloto.
- La cantidad de pipelines crecerá mucho si no se gobierna.

## Recomendaciones RC1

1. Crear estándar oficial de pipeline Host AI.
2. Crear catálogo de pipelines.
3. Clasificar pipelines por estado: core, producción, soporte, legacy, demo.
4. Evitar lógica pesada dentro del pipeline.

## Documentos recomendados

- `DOCS/ESTANDAR_PIPELINES_HOST_AI.md`
- `DOCS/CATALOGO_PIPELINES_HOST_AI.md`

## Prioridad

Media-alta.
