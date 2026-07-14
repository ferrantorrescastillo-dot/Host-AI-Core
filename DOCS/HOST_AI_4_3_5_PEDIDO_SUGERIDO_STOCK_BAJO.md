# Host AI 4.3.5 — Pedido Sugerido desde Stock Bajo

## Objetivo

Convertir las alertas de stock bajo en una propuesta de pedido agrupada por proveedor.

## Fuente

```text
DATOS/db/stock_inicial.json
```

## Salidas

```text
DATOS/db/pedido_sugerido_stock_bajo_4_3_5.json
DATOS/db/pedido_sugerido_stock_bajo_4_3_5.txt
```

## Prueba

```powershell
python TESTS\test_435_pedido_sugerido_stock_bajo.py
```

## Ejecutar con datos reales

```powershell
python APP\pedido_sugerido_stock_bajo_435.py
```
