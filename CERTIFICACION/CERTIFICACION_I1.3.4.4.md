# CERTIFICACIÓN I1.3.4.4

## Resultado
- Tests específicos + escritura segura + importación: **25/25 superados**.
- Compilación: correcta.
- Diagnóstico aislado: `CERTIFICADA`.
- Escrituras en datos de negocio: **0**.
- Informes JSON/TXT: correctos.

## Cobertura
- Estructura de menús.
- Referencias de platos y componentes.
- Catálogos de recetas y artículos.
- Duplicados.
- Food cost y beneficio.
- Resúmenes importados.
- Generación del certificado.

## Nota de regresión
La suite histórica completa incluye un test antiguo que depende del archivo externo `/mnt/data/esc_test/Escandallos Boronat.xlsx`, ausente en este entorno. Ese fallo de fixture no pertenece a I1.3.4.4.
