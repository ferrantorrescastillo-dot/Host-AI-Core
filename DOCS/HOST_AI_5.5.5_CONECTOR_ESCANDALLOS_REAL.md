# HOST AI 5.5.5 — Conector real de escandallos y recetas

Consulta `DATOS/db/escandallos.json` y `articulos.json` en modo solo lectura.

## Consultas soportadas

- `¿En qué recetas uso arroz bomba?`
- `Receta de paella de marisco`
- `Ingredientes de paella de marisco`
- `Escandallo de paella para 150 personas`

Si el escandallo existe, escala cantidades por raciones. Si no existe, informa del dato ausente sin inventar ingredientes.
