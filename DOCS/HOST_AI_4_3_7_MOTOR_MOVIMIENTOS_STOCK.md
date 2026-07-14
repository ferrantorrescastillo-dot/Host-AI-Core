# Host AI 4.3.7 — Motor de Movimientos de Stock

## Objetivo

Registrar entradas, salidas y ajustes de stock con historial.

## Archivos usados

```text
DATOS/db/stock_inicial.json
DATOS/db/stock_movimientos.json
```

## Tipos

```text
entrada
salida
ajuste
```

## Prueba

```powershell
python TESTS\test_437_motor_movimientos_stock.py
```

## Uso real

Entrada:

```powershell
python APP\movimiento_stock_437.py ART000001 entrada 5 "Compra recibida"
```

Salida:

```powershell
python APP\movimiento_stock_437.py ART000001 salida 2 "Producción paella"
```

Ajuste:

```powershell
python APP\movimiento_stock_437.py ART000001 ajuste 10 "Inventario real"
```

## Siguiente paso

```text
Host AI 4.3.8 — Entradas automáticas desde pedidos confirmados
```
