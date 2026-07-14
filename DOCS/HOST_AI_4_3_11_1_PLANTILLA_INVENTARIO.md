# Host AI 4.3.11.1 — Plantilla de Inventario

## Objetivo

Generar un Excel para hacer inventario físico a partir del stock actual.

## Fuente

```text
DATOS/db/stock_inicial.json
```

## Salida

```text
DATOS/inventario_4_3_11_1.xlsx
```

## Columnas

```text
Codigo
Articulo
Unidad
Stock sistema
Stock contado
Diferencia
Ubicación
Proveedor
Familia
Observaciones inventario
```

## Prueba

```powershell
python TESTS\test_43111_plantilla_inventario.py
```

## Generar plantilla real

```powershell
python APP\generar_plantilla_inventario_43111.py
```

## Qué rellenar

Solo rellena:

```text
Stock contado
Observaciones inventario
```

No modifiques:

```text
Codigo
Stock sistema
```

## Siguiente paso

```text
Host AI 4.3.11.2 — Importador de Inventario
```
