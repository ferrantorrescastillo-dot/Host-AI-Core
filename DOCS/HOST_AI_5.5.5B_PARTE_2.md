# HOST AI 5.5.5B — Parte 2

## Objetivo

Interpretar la estructura del libro Excel antes de importar datos.

## Clasificaciones

- ARTICULOS
- FICHAS_TECNICAS
- MENUS
- RESUMENES
- AUXILIARES
- DESCONOCIDAS

## Funciones

- Clasificación por nombre, contenido y señales estructurales.
- Detección preliminar de bloques de fichas técnicas.
- Relación sugerida entre hojas de menú y hojas `M.P`.
- Recomendación de acción por hoja.
- Ejecución estrictamente en modo solo lectura.

## Prueba

```powershell
python TESTS/test_555b_parte2.py
```

## Excel real

```powershell
python APP/analizar_excel_escandallos_555b.py "C:\ruta\archivo.xlsx"
```

Esta parte no importa escandallos ni modifica datos reales.
