# Host AI 4.3.8 — Entrada Stock desde Pedido Confirmado

## Objetivo

Cuando un pedido confirmado llega al restaurante, sumar automáticamente el stock y registrar movimiento.

## Entrada

```text
DATOS/db/pedidos_confirmados.json
```

## Actualiza

```text
DATOS/db/stock_inicial.json
DATOS/db/stock_movimientos.json
```

## Prueba

```powershell
python TESTS\test_438_entrada_stock_desde_pedido.py
```

## Uso real

```powershell
python APP\entrada_stock_desde_pedido_438.py
```

## Flujo

```text
pedido sugerido
↓
pedido confirmado
↓
entrada de stock
↓
movimiento registrado
```
