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

## Biblioteca Culinaria

La Biblioteca es el lugar donde vive el conocimiento culinario reutilizable.
Su taxonomía pública distingue Artículos, Elaboraciones, Recetas, Escandallos,
Fichas técnicas, Menús, Documentación e Importaciones. La nomenclatura técnica
heredada no se muestra en la interfaz: públicamente siempre se habla de
Elaboraciones.

Un Artículo es un producto comprado o ingrediente. Una Elaboración es una
preparación producida por el restaurante; su Receta describe ingredientes y
proceso, su Escandallo contiene los cálculos económicos del backend y su Ficha
técnica reúne la vista operativa viva. Una ficha técnica de proveedor pertenece
al Artículo o a Documentación, no a la ficha culinaria.

La relación de producto es:

`Artículo → Elaboración → Receta → Escandallo → Ficha técnica → Menú → Evento`.

La regla de producto es: cada dato se introduce una vez y se reutiliza. Los
ingredientes solo enlazan con Artículos cuando existe una coincidencia exacta y
única; las coincidencias no demostrables quedan sin relacionar.

Rutas de lectura:

- `GET /api/v1/biblioteca`;
- `GET /api/v1/biblioteca/elaboraciones`;
- `GET /api/v1/biblioteca/elaboraciones/{elaboracion_id}`.

La proyección de Elaboraciones reutiliza dos fuentes existentes, sin crear otra
persistencia: las fichas de `RepositorioBibliotecaRecetas601` y el modelo leído
por `LectorModeloCanonico555B72`. Este último prioriza
`DATOS/db/escandallos_canonicos.json` y conserva el fallback compatible a
`DATOS/db/escandallos.json`. Las fichas 6.0.1 prevalecen cuando comparten código;
el resto de escandallos canónicos se proyecta como elaboraciones parciales.

La regla de clasificación no usa el catálogo de Artículos: solo una receta
contenida en el modelo de escandallos puede aparecer como Elaboración. Su código
de receta es el identificador público estable; si un registro heredado carece de
código, la capa de lectura genera una identidad determinista a partir de nombre,
rendimiento y unidad. Una elaboración canónica tiene receta y escandallo cuando
contiene ingredientes reales, pero solo declara ficha técnica, procedimiento,
documentos, menús o eventos si esas relaciones existen en la fuente.

Los ingredientes conservan su `articulo_id` únicamente cuando resuelve contra el
Catálogo Maestro; la coincidencia exacta y única por nombre se mantiene como
compatibilidad. No se realizan emparejamientos aproximados silenciosos. La
nomenclatura interna heredada se conserva en origen, pero se traduce a
«Elaboración» en el contrato y la interfaz públicos.

Menús, documentos e importaciones disponen de espacios públicos preparados,
pero no simulan capacidades. La escritura web queda aplazada hasta incorporar
confirmación y auditoría pública. En una fase posterior, las recetas podrán
originarse desde Word, PDF o imagen: la IA detectará, interpretará, relacionará
y propondrá; el backend validará y el usuario revisará y confirmará. Los menús
podrán duplicarse y reutilizarse entre eventos mediante sus casos de uso.
