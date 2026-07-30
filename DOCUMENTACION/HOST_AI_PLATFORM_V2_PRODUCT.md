# Host AI Platform V2 — Catálogo web de artículos

La primera ampliación V2 publica una vista de solo lectura del catálogo maestro ya
existente. No crea una fuente alternativa ni permite escrituras.

## Arquitectura

`CatalogoMaestroProductos601` → `ArticulosCatalogReadService` → fachada pública →
`GET /api/v1/articulos` y `GET /api/v1/articulos/{articulo_id}` → servicio React.

La identidad pública estable es `codigo`, expuesta también como `id`. El stock se
relaciona primero por `articulo_id` y, solo como compatibilidad con registros
históricos sin identificador, por nombre normalizado exacto.

## Listado

`GET /api/v1/articulos` acepta `q`, `familia`, `proveedor`, `estado`,
`con_stock`, `page`, `page_size` (máximo 100), `orden` y `direccion`.
`q` busca por nombre, código, familia o proveedor. La respuesta contiene:

- `catalogo.items`: resúmenes con identidad, clasificación, proveedor, precio,
  stock, estado y fecha de actualización;
- `total`, `page`, `page_size`, `total_pages`;
- opciones reales en `filtros`;
- `capacidades`, que declara las relaciones verificables.

Los filtros desconocidos y valores inválidos producen un error HTTP 400 estable.

## Detalle

`GET /api/v1/articulos/{articulo_id}` devuelve `articulo` con datos maestros,
stock y lotes, asociaciones de proveedor, precios e historial. Devuelve HTTP 404
si la identidad no existe.

Documentos, ficha técnica, recetas y escandallos se mantienen vacíos mientras el
proyecto no disponga de una relación verificable por identificador estable. No se
infieren relaciones mediante coincidencias aproximadas.

Todas las respuestas conservan el sobre público (`ok`, versiones, `request_id`,
`modo_seguro` y `datos_reales_modificados`). Las consultas son de solo lectura.
