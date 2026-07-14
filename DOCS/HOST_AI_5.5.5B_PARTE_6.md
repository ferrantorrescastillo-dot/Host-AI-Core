# HOST AI 5.5.5B — Parte 6

## Objetivo

Resolver de forma segura los casos que la preimportación dejó pendientes:

- duplicados exactos;
- recetas casi iguales con diferencias menores;
- variantes reales con el mismo nombre;
- títulos inválidos como `KG`;
- selección de la ficha más completa y fiable.

## Principio de seguridad

La Parte 6 **no importa ni modifica datos**. Solo genera un informe de decisiones.

Las decisiones automáticas se limitan a duplicados equivalentes. Las fusiones, variantes y correcciones de títulos requieren confirmación humana.

## Uso

```powershell
python TESTS/test_555b_parte6.py
```

```powershell
python APP/resolver_variantes_escandallos_555b.py "RUTA_EXCEL.xlsx" --preimportacion "DATOS\informes\preimportacion_555b.json"
```

El informe se guarda por defecto en:

```text
DATOS/informes/resolucion_variantes_555b.json
```

## Resultado

- `SELECCIONAR_MEJOR_FICHA`: duplicados equivalentes; se recomienda conservar la ficha con mayor confianza y más enlaces.
- `FUSIONAR_DUPLICADOS`: fichas muy parecidas con pequeñas diferencias; requiere revisión.
- `MANTENER_COMO_VARIANTES`: composiciones distintas; propone nombres diferenciados usando la hoja de origen.
- `REVISAR_TITULO`: el título no parece una receta y no se inventa un nombre alternativo.
