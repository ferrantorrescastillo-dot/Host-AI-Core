# Host AI 4.3.11.2 — Importador de Inventario

## Objetivo

Leer la plantilla de inventario rellenada y guardar el inventario contado.

## Entrada

```text
DATOS/inventario_4_3_11_1.xlsx
```

## Salida

```text
DATOS/db/inventario_contado_4_3_11_2.json
```

## Importante

Este módulo **no modifica el stock todavía**.

Solo guarda:

```text
stock sistema
stock contado
diferencia
observaciones
```

## Prueba

```powershell
python TESTS\test_43112_importador_inventario.py
```

## Ejecutar con datos reales

```powershell
python APP\importar_inventario_43112.py
```

## Siguiente paso

```text
Host AI 4.3.11.3 — Comparador de Inventario
```
