# Host AI 4.3.11.3 — Comparador Inteligente de Inventario

## Objetivo

Comparar stock sistema vs stock contado.

## Entrada

```text
DATOS/db/inventario_contado_4_3_11_2.json
```

## Salidas

```text
DATOS/db/comparacion_inventario_4_3_11_3.json
DATOS/db/comparacion_inventario_4_3_11_3.txt
```

## Importante

Este módulo no modifica el stock.

Solo clasifica:

```text
ok
faltante
sobrante
revisar
```

## Prueba

```powershell
python TESTS\test_43113_comparador_inventario.py
```

## Ejecutar con datos reales

```powershell
python APP\comparar_inventario_43113.py
```

## Siguiente paso

```text
Host AI 4.3.11.4 — Aplicador de Ajustes de Inventario
```
