# HOST AI 5.5.5B.7.3 — Escandallo económico y rentabilidad

Amplía la consulta conversacional de escandallos con una lectura económica profesional:

- coste total de receta;
- coste por unidad/ración;
- precio de venta opcional;
- beneficio bruto unitario;
- beneficio sobre coste;
- margen bruto sobre venta;
- food cost;
- IVA opcional;
- aviso de ingredientes sin precio;
- estado económico.

## Seguridad

El parche es de solo lectura. No cambia precios, recetas ni escandallos.
Si no existe precio de venta, no lo inventa y deja los porcentajes dependientes del PVP como pendientes.

## Campos opcionales admitidos en el modelo canónico

- `precio_venta_unitario`
- `precio_venta`
- `pvp_unitario`
- `pvp`
- `iva_pct`

Pueden estar en el escandallo o dentro de `receta`.

## Prueba

```powershell
python TESTS/test_555b73_escandallo_economico.py
```

Después reinicia Host AI y consulta:

```text
Muéstrame el escandallo de ensaladilla de gamba.
```
