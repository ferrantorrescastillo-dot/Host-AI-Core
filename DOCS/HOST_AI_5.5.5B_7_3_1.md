# HOST AI 5.5.5B.7.3.1

## Enriquecimiento económico desde artículos

Este parche conecta las líneas del escandallo canónico con `DATOS/db/articulos.json` para recuperar precios reales sin duplicarlos dentro de cada receta.

### Orden de enlace

1. Código interno exacto (`articulo_id`).
2. Nombre normalizado exacto.
3. Nombre aproximado solo cuando la coincidencia es inequívoca y de alta confianza.

### Seguridad

- Solo lectura.
- No modifica escandallos ni artículos.
- No inventa precios.
- Los enlaces ambiguos quedan marcados para revisión.
- El precio ya presente en la línea del escandallo tiene prioridad sobre el catálogo.

### Resultado económico

La consulta de un escandallo muestra:

- coste total;
- coste por rendimiento;
- ingredientes valorados/total;
- ingredientes sin precio;
- fuente de precios;
- estado económico completo o parcial.
