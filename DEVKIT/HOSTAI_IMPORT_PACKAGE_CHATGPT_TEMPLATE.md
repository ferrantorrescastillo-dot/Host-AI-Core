# Plantilla histórica compatible

La plantilla oficial vendor-neutral está en `DEVKIT/HOSTAI_IMPORT_PACKAGE_AI_TEMPLATE.md`. Este nombre se conserva como referencia de compatibilidad para paquetes ya preparados; todos usan el mismo contrato `hostai.import.package` versión `0.1`.

# Ejemplo histórico: ChatGPT externo → Host AI

Usa esta instrucción al entregar un documento a ChatGPT:

> Interpreta el documento y devuelve exclusivamente JSON compatible con `hostai.import.package`, versión `0.1`. Describe información observada, interpretación semántica, confianza y procedencia. Declara dudas; no inventes datos ni expliques razonamiento interno.

## Estructura mínima

```json
{
  "schema": "hostai.import.package",
  "version": "0.1",
  "metadata": {
    "source": {
      "kind": "XLSX",
      "original_filename": "archivo.xlsx",
      "sha256": "solo si fue calculado"
    },
    "extractor": {"name": "CHATGPT_EXTERNAL", "version": "versión conocida"}
  },
  "recipes": [],
  "articles": [],
  "suppliers": [],
  "menus": [],
  "relations": [],
  "ambiguities": [],
  "variant_groups": []
}
```

## Significado

- `recipes`: recetas, elaboraciones o subelaboraciones con `name`, `ingredients`, rendimiento, procedimiento, costes documentales, `occurrences`, `observed`, `interpretation`, `confidence` y `provenance` cuando existan.
- `articles`: artículos observados. Usa `source_code`, nunca IDs canónicos Host AI. Un precio va en `document_price` y es solo referencia documental.
- `menus`: bloques que no son recetas. Usa `kind`: `MENU`, `CONTENEDOR`, `CONTEXT` o `PRODUCTO_VENDIBLE`.
- `relations`: relaciones observadas entre recetas, subelaboraciones, artículos, productos o menús.
- `ambiguities`: dudas explícitas con `type`, `name`, `reason`, opciones y provenance.
- `variant_groups`: versiones con diferencias materiales. No fusiones variantes silenciosamente.
- `occurrences`: varias apariciones de una misma interpretación lógica, conservando hoja, fila o región.

## Reglas obligatorias

- No inventar `article_id`, `recipe_id`, `supplier_id` ni ningún ID canónico.
- No inventar ni modificar stock, lotes, movimientos, recepciones, compras, facturas o permisos.
- No declarar un proveedor observado como proveedor real o habitual.
- No declarar un precio documental como precio real de compra.
- No convertir etiquetas o encabezados en recetas.
- No forzar menús o contenedores a recetas.
- Si no hay evidencia suficiente, añadir una ambigüedad.
- No incluir chain-of-thought. Solo entidades, relaciones, contexto, dudas y provenance observables.

El JSON Schema oficial se exporta desde el modelo real con:

```text
python -m SCRIPTS.export_hostai_import_package_schema <destino.json>
```
