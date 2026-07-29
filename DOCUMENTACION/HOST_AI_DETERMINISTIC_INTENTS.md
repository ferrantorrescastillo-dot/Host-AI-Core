# HOST AI DETERMINISTIC INTENTS

Estado: Implementado en APP-01.5
Fecha: 2026-07-23

## 1. Catalogo de intenciones

1. BUSCAR_RECETA
2. LISTAR_RECETAS_PENDIENTES
3. LISTAR_ESCANDALLOS_DESACTUALIZADOS
4. LISTAR_INCIDENCIAS
5. MOSTRAR_EVENTOS_PROXIMOS
6. ABRIR_MODULO
7. MOSTRAR_ESTADO_GENERAL
8. AYUDA

## 2. Router

Servicio: HostAIDeterministicIntentRouter

Reglas:

- normalizacion a minusculas;
- limpieza controlada de signos;
- patrones simples de palabras clave;
- extraccion limitada de termino de receta;
- mapeo de modulo por keywords.

## 3. Patrones reconocidos (ejemplos)

- "Busca la receta paella" -> BUSCAR_RECETA
- "Muestrame las recetas pendientes" -> LISTAR_RECETAS_PENDIENTES
- "Que escandallos estan desactualizados" -> LISTAR_ESCANDALLOS_DESACTUALIZADOS
- "Que incidencias tengo" -> LISTAR_INCIDENCIAS
- "Que eventos hay proximos" -> MOSTRAR_EVENTOS_PROXIMOS
- "Abre produccion" / "Llevame a compras" -> ABRIR_MODULO
- "Como esta el sistema" -> MOSTRAR_ESTADO_GENERAL
- "Ayuda" -> AYUDA

## 4. Servicios llamados

Flujo:

Usuario -> Chat UI -> ServicioChatHostAIShell -> Intent Router
-> Orquestador/HostAIEngine (SIMULADO) -> HostAIHomeReadService / servicio de lectura
-> respuesta normalizada

## 5. Respuestas y tipos

Tipos usados:

- RESULTADO
- ADVERTENCIA
- AYUDA
- ERROR

Las respuestas incluyen, cuando aplica:

- resultados limitados
- accion_navegacion segura (solo abrir)
- estado de engine simulado

## 6. Limites de APP-01.5

- No hay NLP libre avanzado.
- No hay escritura de negocio.
- No hay ejecucion de herramientas externas.
- No hay memoria persistente de chat largo.

## 7. Ambiguedad

Si no hay certeza:

- respuesta segura de advertencia
- no se ejecuta accion
- no se adivina destino

Referencia de sesion soportada:

- "abre la primera" cuando el resultado previo es BUSCAR_RECETA.

## 8. Migracion futura a IA real

Preparado para evolucion:

- conservar catalogo determinista como fallback seguro;
- introducir clasificador IA gradual sin eliminar reglas transparentes;
- mantener policy y confirmaciones para cualquier futura escritura.
