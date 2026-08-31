# HostAIImportPackage 0.1

`HostAIImportPackage` es el contrato de intercambio versionado para interpretaciones externas. No es un formato de escritura ni una fuente de identidad canónica.

```json
{
  "schema": "hostai.import.package",
  "version": "0.1",
  "metadata": {
    "source": "sistema externo",
    "generated_at": "2026-08-28T12:00:00Z"
  },
  "recipes": [{
    "source_id": "REC-EXT-1",
    "name": "Salsa de naranja",
    "ingredients": [{"name": "Naranja", "quantity": 1, "unit": "kg"}],
    "procedure": ["Reducir"],
    "yield": 1,
    "yield_unit": "kg",
    "observed": {"name": "SALSA NARANJA"},
    "interpretation": {"entity_type": "ELABORACION_INTERNA"},
    "confidence": 0.92,
    "provenance": {"page": 2, "region": "A12:F20"}
  }],
  "articles": [{
    "source_code": "EXT-10",
    "name": "Naranja",
    "unit": "kg",
    "document_price": {
      "value": 1.25,
      "currency": "EUR",
      "format": "caja 5 kg",
      "unit": "kg",
      "context": "tarifa observada"
    },
    "provenance": {"sheet": "Artículos", "row": 10}
  }],
  "suppliers": [],
  "menus": [],
  "relations": [],
  "ambiguities": [],
  "variant_groups": []
}
```

El adaptador valida `schema` y `version`, rechaza campos con autoridad operativa (stock, lotes, movimientos, compras, permisos e identificadores canónicos arbitrarios), ignora campos desconocidos y convierte las colecciones al modelo intermedio del importador existente. Matching, reutilización, variantes, PREVIEW y CONFIRM siguen gobernados por los componentes canónicos actuales.

Los precios externos se conservan exclusivamente como referencias importadas no aplicables. ANALYZE y PREVIEW realizan cero escrituras operativas. Solo CONFIRM puede escribir mediante el flujo seguro existente.

El prototipo histórico `hostai.chatgpt_import.v0.1` no es compatible directamente. Su migración explícita se realiza con `SCRIPTS/convert_hostai_chatgpt_import_v01.py`; nunca se interpreta silenciosamente como el contrato definitivo.

El JSON Schema oficial se genera desde las constantes y la representación del modelo con `SCRIPTS/export_hostai_import_package_schema.py`. La plantilla neutral para herramientas de IA externas está en `DEVKIT/HOSTAI_IMPORT_PACKAGE_AI_TEMPLATE.md`.
