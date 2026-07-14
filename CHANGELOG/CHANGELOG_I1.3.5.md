# I1.3.5 — Refactorización y certificación final del importador

## Cambios
- Centralización de huellas de incidencias, filtros, agrupaciones y coincidencias exactas.
- Refactorización de I1.3.4.4.2 para reutilizar contratos comunes sin cambiar su comportamiento.
- Nueva opción 34 para ejecutar la certificación final de la línea I1.3.
- Generación de informe JSON y TXT de certificación en `DATOS/certificaciones/i135/`.
- Comprobación de carga de módulos críticos y huellas de archivos de negocio.

## Seguridad
- Diagnóstico de solo lectura sobre menús, recetas y artículos.
- No añade funcionalidad operativa nueva.
- No modifica datos de negocio.
