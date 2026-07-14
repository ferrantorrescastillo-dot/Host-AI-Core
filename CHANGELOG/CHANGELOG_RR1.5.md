# HOST AI 6.0.4 — RR1.5 Pulido de IA

## Objetivo
Pulir la experiencia conversacional de IA1 sin ejecutar acciones ni introducir IA2.

## Cambios
- Nueva capa `PulidoIARR15` sobre IA1.4.
- Respuestas naturales orientadas a cocina, no técnicas.
- Reutilización automática de evento, plan, pedido y receta activos.
- Menos preguntas repetidas cuando el contexto ya contiene el dato.
- Preguntas centradas solo en los campos realmente faltantes.
- Resúmenes claros de consultas y modificaciones propuestas.
- Confirmación explícita para cualquier modificación.
- Ejemplos útiles cuando la frase no se entiende.
- Modo seguro preservado: no ejecuta motores ni modifica datos.
- Opción 11 del Base renombrada a RR1.5 IA pulida.

## Instalación
1. Cierra Host AI.
2. Haz una copia completa de la carpeta actual.
3. Copia el contenido de este parche sobre la raíz de Host AI.
4. Acepta reemplazar los archivos existentes.
5. Ejecuta `python main.py`.

## Validación
- 90 pruebas superadas.
- 0 fallos.
- 0 errores de colección.
