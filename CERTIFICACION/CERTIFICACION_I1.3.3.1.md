# CERTIFICACIÓN I1.3.3.1

## Alcance certificado
- Vincular un bloqueo con una receta existente.
- Crear una receta real y mínima con ingredientes catalogados.
- Rechazar recetas sin ingredientes o rendimiento válido.
- Crear backup antes de escribir recetas.
- Actualizar el aprendizaje existente conservando la clave original y el historial.
- Recalcular automáticamente la preimportación.
- Marcar `LISTA` únicamente con cero bloqueos.
- Mantener `importacion_disponible = False`.

## Resultado
- Tests del bloque I1.3 y regresión legacy: 35/35 superados.
- Compilación de consola y servicio: correcta.
- Importación definitiva de menús: deshabilitada.
