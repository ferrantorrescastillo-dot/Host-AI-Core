# Host AI 4.1.9.1 — Fix Clasificador de Familias

## Problema detectado

`Coca Cola 33cl` se clasificaba mal porque la palabra `coca` estaba dentro de reglas de panadería.

## Corrección

- Se añade regla prioritaria para bebidas.
- `Coca Cola` pasa a `Bebidas`.
- `Coca de recapte` sigue pudiendo ir a `Panadería`.

## Prueba

```powershell
python TESTS\test_419_clasificador_familias_articulos.py
```

## Ejecutar sobre datos reales

```powershell
python APP\clasificar_familias_articulos_419.py
python APP\informe_catalogo_articulos_418.py
```
