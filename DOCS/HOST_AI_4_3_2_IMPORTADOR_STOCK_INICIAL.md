# Host AI 4.3.2 — Importador de Stock Inicial

## Objetivo

Importar el Excel rellenado de stock inicial a:

```text
DATOS/db/stock_inicial.json
```

## Entrada esperada

```text
DATOS/stock_inicial_4_3_1.xlsx
```

Hoja:

```text
Stock inicial
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
python TESTS\test_432_importador_stock_inicial.py
```

## Importar stock real

```powershell
python APP\importar_stock_inicial_432.py
```

O indicando ruta:

```powershell
python APP\importar_stock_inicial_432.py "C:\Proyecto Host IA 3.0\DATOS\stock_inicial_4_3_1.xlsx"
```

## Importante

Las filas sin unidad, sin stock actual y sin stock mínimo se ignoran como no rellenadas.

## Siguiente paso

Después de importar, crearemos:

```text
Host AI 4.3.3 — Informe de Stock Inicial
```
