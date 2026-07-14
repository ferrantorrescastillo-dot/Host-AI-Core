# Host AI 4.3.9 — Salidas Manuales de Stock

## Objetivo

Registrar salidas de stock por producción, merma, rotura, consumo interno o ajuste operativo.

## Usa

```text
SERVICIOS/motor_movimientos_stock_437.py
```

## Actualiza

```text
DATOS/db/stock_inicial.json
DATOS/db/stock_movimientos.json
```

## Prueba

```powershell
python TESTS\test_439_salidas_stock.py
```

## Uso real

Producción:

```powershell
python APP\salida_stock_439.py ART000001 2 produccion "Producción paella"
```

Merma:

```powershell
python APP\salida_stock_439.py ART000001 1 merma "Producto caducado"
```

Rotura:

```powershell
python APP\salida_stock_439.py ART000001 1 rotura "Botella rota"
```

## Siguiente paso

```text
Host AI 4.3.10 — Historial de movimientos de stock
```
