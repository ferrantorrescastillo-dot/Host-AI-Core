# HOST AI 5.5.5B — Parte 3

## Objetivo

Extraer recetas e ingredientes desde los bloques de ficha técnica detectados en Excel y convertirlos a una vista previa normalizada compatible con el modelo canónico 5.5.5A.

## Alcance

- Detecta todos los marcadores `FICHA TÉCNICA` del libro, sin limitarse a las primeras 80 filas.
- Obtiene nombre de receta, rendimiento, unidad e ingredientes.
- Conserva hoja y fila de origen para trazabilidad.
- Señala fichas incompletas para revisión.
- Genera una representación canónica en modo vista previa.

## Seguridad

Esta parte no guarda escandallos, no sobrescribe la base interna y no modifica el Excel. La escritura confirmada se implementará en una fase posterior.

## Pruebas

```powershell
python TESTS/test_555b_parte3.py
python APP/extraer_fichas_tecnicas_555b.py "C:\ruta\archivo.xlsx"
```
