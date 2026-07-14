# HOST AI 6.0.4 — RR1.4 Pulido de Escandallos y Costes

## Objetivo
Corregir los problemas detectados durante la prueba Restaurant Ready en Escandallos y Costes, sin añadir motores paralelos ni modificar el resto de módulos certificados.

## Cambios
- Se mantiene una receta activa entre operaciones para evitar búsquedas repetidas.
- El menú de Escandallos muestra recetas activas y recetas sin ingredientes.
- Se bloquean cálculos económicos y simulaciones de recetas vacías.
- Se elimina el falso resultado de 100 % de margen en recetas sin ingredientes.
- Costes permite seleccionar una receta real por nombre o código.
- Registrar precio utiliza el buscador común de artículos y conserva ID, familia y proveedor.
- El cálculo de coste de receta muestra el mismo detalle operativo de ES2.
- La simulación selecciona automáticamente el ingrediente cuando solo existe uno.
- Los resúmenes globales vacíos explican qué cálculo debe realizarse primero.
- Mensajes de cancelación y validación más claros.

## Validación
- 85 pruebas superadas.
- 0 fallos.
- 0 errores de colección.
