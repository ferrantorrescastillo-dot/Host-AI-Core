# Host AI 4.3.3 — Informe de Stock Inicial

## Objetivo

Analizar el stock inicial importado desde:

```text
DATOS/db/stock_inicial.json
```

comparándolo con:

```text
DATOS/db/articulos.json
```

## Prueba

```powershell
python TESTS\test_433_informe_stock_inicial.py
```

## Ejecutar informe real

```powershell
python APP\informe_stock_inicial_433.py
```

## Archivo generado

```text
DATOS/db/informe_stock_inicial_4_3_3.txt
```

## Estados

```text
sin_datos
apto
apto_con_observaciones
no_apto
```
