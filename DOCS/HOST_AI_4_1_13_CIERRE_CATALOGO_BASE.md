# Host AI 4.1.13 — Cierre Catálogo Base

## Objetivo

Cerrar el primer bloque real de datos base:

```text
Artículos
Proveedores
Familias
Precios
```

## Prueba

```powershell
python TESTS\test_4113_cierre_catalogo_base.py
```

## Ejecutar con datos reales

```powershell
python APP\cierre_catalogo_base_4113.py
```

## Archivo generado

```text
DATOS/db/cierre_catalogo_base_4_1_13.txt
```

## Resultado

Puede devolver:

```text
apto
apto_con_observaciones
no_apto
```

Si sale `apto` o `apto_con_observaciones`, podemos pasar a:

```text
Host AI 4.3 - Stock inicial real
```
