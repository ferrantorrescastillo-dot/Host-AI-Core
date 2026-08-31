# Plantilla de IA externa → Host AI

Analiza el documento incluido.

Genera como resultado un archivo JSON compatible con:

```text
schema: hostai.import.package
version: 0.1
```

Sigue estrictamente el JSON Schema incluido. No inventes identificadores canónicos de Host AI. Cuando exista incertidumbre, declárala.

Esta instrucción es independiente del proveedor o modelo. Entrégala a cualquier herramienta de IA junto con el documento original y el JSON Schema oficial de `HostAIImportPackage 0.1`.

> Interpreta el documento y devuelve exclusivamente JSON compatible con `hostai.import.package`, versión `0.1`. Describe solo información observable, interpretación semántica, confianza y procedencia. Declara las incertidumbres; no inventes datos ni expongas razonamiento interno.

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
    "extractor": {
      "name": "nombre opcional de la herramienta",
      "version": "versión opcional",
      "generated_at": "fecha opcional si es conocida"
    }
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

## Contenido observable

- `recipes`: recetas, elaboraciones y subelaboraciones, incluidos ingredientes, rendimiento, procedimiento, `occurrences`, `observed`, `interpretation`, `confidence` y `provenance` cuando existan.
- `articles`: artículos observados. Usa `source_code`; nunca IDs canónicos de Host AI.
- `menus`: menús y otros contenedores o contextos. Usa `kind`: `MENU`, `CONTENEDOR`, `CONTEXT` o `PRODUCTO_VENDIBLE`.
- `relations`: relaciones observadas entre recetas, subelaboraciones, artículos, productos y menús.
- `ambiguities`: dudas explícitas, su motivo, opciones y procedencia.
- `variant_groups`: variantes con diferencias materiales; no deben fusionarse silenciosamente.
- `occurrences`: apariciones de una interpretación lógica, conservando hoja, fila o región.
- `provenance`: fuente concreta de cada dato cuando pueda determinarse.

## Reglas obligatorias

- Cada elemento de `recipes`, `articles`, `suppliers` y `menus` debe incluir `name`; `name_observed` no sustituye el nombre contractual.
- No inventar `article_id`, `recipe_id`, `supplier_id` ni otro ID canónico.
- No inventar stock, lotes, movimientos, compras, recepciones o facturas.
- No inventar un proveedor real o habitual.
- No inventar un precio real; un precio observado solo puede declararse como referencia documental.
- No convertir etiquetas, encabezados, menús o contextos en recetas sin evidencia.
- Declarar una ambigüedad cuando la evidencia sea insuficiente.
- No incluir chain-of-thought. Entregar solo el contrato observable.

El generador no tiene autoridad sobre identidades ni datos operativos. Host AI aplica siempre la misma validación, sanitización, matching, PREVIEW y CONFIRM.

El JSON Schema oficial se exporta desde el modelo real con:

```text
python -m SCRIPTS.export_hostai_import_package_schema <destino.json>
```
