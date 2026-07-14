# HOST AI 5.5.5B Parte 3 — Fix de rendimiento

Corrige una lentitud extrema al analizar libros Excel reales.

## Causa

`openpyxl` se abría en modo `read_only=True` y el extractor realizaba accesos
aleatorios con `hoja.cell(...)`. En ese modo, cada acceso puede volver a
recorrer el XML de la hoja, provocando esperas muy largas.

## Corrección

- El libro se carga en modo normal con `data_only=True`.
- El Excel sigue tratándose en solo lectura lógica: no se guarda ni se modifica.
- La detección de marcadores se hace en una sola pasada.

## Seguridad

- No se escribe en el Excel.
- No se importan escandallos todavía.
- No se modifican datos reales.
