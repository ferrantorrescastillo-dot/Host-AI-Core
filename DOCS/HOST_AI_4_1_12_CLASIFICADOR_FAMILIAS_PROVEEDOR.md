# Host AI 4.1.12 — Clasificador de Familias por Proveedor

## Objetivo

Reducir artículos pendientes de familia usando proveedor + palabras del nombre.

## No pisa familias existentes

Solo actúa sobre artículos sin familia.

## Prueba

```powershell
python TESTS\test_4112_clasificador_familias_proveedor.py
```

## Ejecutar con datos reales

```powershell
python APP\clasificar_familias_proveedor_4112.py
python APP\informe_pendientes_familia_4110.py
python APP\informe_catalogo_articulos_418.py
```
