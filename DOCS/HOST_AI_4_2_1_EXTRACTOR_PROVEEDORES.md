# Host AI 4.2.1 — Extractor de Proveedores

## Objetivo

Crear la primera base real de proveedores desde los artículos importados.

## Entrada

```text
DATOS/db/articulos.json
```

## Salida

```text
DATOS/db/proveedores.json
```

## Qué detecta

- Proveedores distintos.
- Artículos sin proveedor.
- Variantes sospechosas del mismo proveedor:
  - Makro
  - MAKRO
  - Makro.

## Comando de prueba

```powershell
python TESTS\test_421_extractor_proveedores.py
```

## Ejecutar con datos reales

```powershell
python APP\extraer_proveedores_421.py
```

## Siguiente paso

Revisar `proveedores.json` y pasar a 4.2.2: normalizador/editor de proveedores.
