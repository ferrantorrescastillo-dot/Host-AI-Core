# Host AI 4.1.11 — Editor Manual de Familias

## Objetivo

Asignar manualmente familia a los artículos que siguen pendientes después del clasificador 4.1.9.

## Prueba

```powershell
python TESTS\test_4111_editor_familias_articulos.py
```

## Uso por código

```powershell
python APP\asignar_familia_4111.py ART000123 "Varios"
```

## Uso por nombre exacto

```powershell
python APP\asignar_familia_4111.py "Arroz bomba" "Arroces y cereales"
```

## Después

Volver a ejecutar:

```powershell
python APP\informe_pendientes_familia_4110.py
python APP\informe_catalogo_articulos_418.py
```
