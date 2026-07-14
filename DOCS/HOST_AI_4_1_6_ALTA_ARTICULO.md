# Host AI 4.1.6 — Alta Manual de Artículos

## Objetivo

Añadir artículos nuevos directamente a:

```text
DATOS/db/articulos.json
```

Sin tocar el Excel.

## Comando de prueba

```powershell
python TESTS\test_416_alta_articulo.py
```

## Uso

```powershell
python APP\alta_articulo_416.py "Arroz bomba" "Makro" "Arroces" "3,20"
```

Después buscar:

```powershell
python APP\buscar_articulos_415.py "arroz bomba"
```

## Regla

- Si no pasas código, genera el siguiente `ART000XXX`.
- Si el nombre ya existe exacto, no duplica.
- Si el código existe, no duplica.
