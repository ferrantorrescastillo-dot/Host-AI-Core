# Host AI 4.3.6 — Confirmar Pedido Sugerido

## Objetivo

Convertir el pedido sugerido generado por stock bajo en pedidos confirmados.

## Entrada

```text
DATOS/db/pedido_sugerido_stock_bajo_4_3_5.json
```

## Salida

```text
DATOS/db/pedidos_confirmados.json
```

## Prueba

```powershell
python TESTS\test_436_confirmador_pedido_sugerido.py
```

## Ejecutar con datos reales

```powershell
python APP\confirmar_pedido_sugerido_436.py
```

## Flujo

```text
Stock bajo
↓
Pedido sugerido
↓
Pedido confirmado
```
