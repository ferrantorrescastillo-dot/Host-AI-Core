# Host AI 4.1.9 — Clasificador de Familias de Artículos

## Objetivo

Rellenar familias vacías en:

```text
DATOS/db/articulos.json
```

## Regla

- Solo rellena artículos sin familia.
- No pisa familias existentes.
- Usa reglas culinarias simples.

## Prueba

```powershell
python TESTS\test_419_clasificador_familias_articulos.py
```

## Ejecutar con datos reales

```powershell
python APP\clasificar_familias_articulos_419.py
```

## Después

Volver a ejecutar:

```powershell
python APP\informe_catalogo_articulos_418.py
```

Objetivo: reducir `Sin familia`.
