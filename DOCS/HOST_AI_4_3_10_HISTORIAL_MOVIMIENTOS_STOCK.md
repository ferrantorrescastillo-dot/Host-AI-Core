# Host AI 4.3.10 — Historial de Movimientos de Stock

## Objetivo

Consultar qué ha pasado con el stock.

## Fuente

```text
DATOS/db/stock_movimientos.json
```

## Prueba

```powershell
python TESTS\test_4310_historial_movimientos_stock.py
```

## Uso general

```powershell
python APP\historial_movimientos_stock_4310.py
```

## Filtrar por artículo

```powershell
python APP\historial_movimientos_stock_4310.py ART000001
```

## Filtrar por tipo

Usa `-` para no filtrar código:

```powershell
python APP\historial_movimientos_stock_4310.py - salida
python APP\historial_movimientos_stock_4310.py - entrada
python APP\historial_movimientos_stock_4310.py - ajuste
```

## Archivo generado

```text
DATOS/db/historial_movimientos_stock_4_3_10.txt
```
