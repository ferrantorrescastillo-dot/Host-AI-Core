# HOST AI 5.5.5B — Parte 4

## Objetivo

Depurar la vista previa extraída en la Parte 3 antes de cualquier importación.

## Funciones

- Rechaza o marca títulos genéricos que no parecen recetas (`KG`, `U`, cabeceras, etc.).
- Detecta recetas repetidas y diferencia duplicados exactos de variantes con el mismo nombre.
- Detecta ingredientes que en realidad son elaboraciones ya presentes como receta.
- Normaliza unidades únicamente cuando la corrección es inequívoca.
- Clasifica cada ficha como `PREPARADA`, `REVISAR` o `RECHAZADA`.
- Conserva hoja y filas de origen para auditoría.

## Seguridad

Esta fase es solo lectura. No modifica el Excel, no guarda escandallos y no altera la base de datos.

## Ejecución

```powershell
python TESTS/test_555b_parte4.py
python APP/depurar_fichas_tecnicas_555b.py "C:\ruta\archivo.xlsx"
```

## Siguiente fase

La Parte 5 realizará la preimportación controlada: comparación con el modelo canónico, relación con artículos y confirmación antes de guardar.
