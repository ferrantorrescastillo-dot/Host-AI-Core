# Host AI 4.3.1 — Plantilla de Stock Inicial

## Objetivo

Generar una plantilla Excel para rellenar stock real del restaurante.

## Fuente

```text
DATOS/db/articulos.json
```

## Salida

```text
DATOS/stock_inicial_4_3_1.xlsx
```

## Columnas

```text
Codigo
Articulo
Proveedor
Familia
Unidad
Stock actual
Stock mínimo
Ubicación
Observaciones stock
```

## Prueba

```powershell
python TESTS\test_431_plantilla_stock_inicial.py
```

## Generar plantilla real

```powershell
python APP\generar_plantilla_stock_431.py
```

## Qué hacer después

Abrir el Excel generado y rellenar:

- Unidad
- Stock actual
- Stock mínimo
- Ubicación

Después pasaremos a:

```text
Host AI 4.3.2 — Importador de Stock Inicial
```
