# Arquitectura técnica M1.3.3

## Objetivo
Añadir una capa de validación culinaria explicable entre la resolución de ingredientes y la creación definitiva de la receta.

## Entrada
`BorradorRecetaM131` ya resuelto por M1.3.2 y el catálogo de artículos utilizado por el flujo.

## Salida
`ResultadoValidacionM133` con:
- estado global;
- errores bloqueantes;
- avisos revisables;
- informativos;
- coste conocido total y por ración;
- listado de hallazgos explicables.

## Severidades
- `ERROR`: impide crear la receta.
- `AVISO`: requiere revisión, pero no bloquea automáticamente.
- `INFO`: observación no crítica.

## Reglas críticas
- nombre obligatorio;
- rendimiento mayor que cero;
- al menos un ingrediente;
- cantidad positiva;
- unidad presente;
- artículo real vinculado;
- prohibición de usar `A.P` como materia prima automática.

## Reglas revisables
- duplicados;
- cantidades extraordinarias;
- unidades no normalizadas o sospechosas;
- coste extraordinariamente alto o bajo;
- artículos sin precio;
- falta de elaboración, tiempos, conservación o revisión de alérgenos.

## Filosofía
El validador no pretende imponer una única cocina correcta. Solo bloquea incoherencias objetivas y presenta como aviso aquello que puede ser válido según la técnica, el producto o el establecimiento.

## Fuera de alcance
- crear o guardar la receta;
- corregir automáticamente cantidades;
- inventar tiempos o alérgenos;
- sustituir la validación del chef;
- importar definitivamente menús.
