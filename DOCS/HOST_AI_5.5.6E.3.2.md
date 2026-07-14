# HOST AI 5.5.6E.3.2 — Ingesta de recetas en lenguaje natural

Permite pegar un proceso real escrito por un cocinero, ChatGPT u otra fuente, convertirlo en fases estructuradas y guardarlo únicamente tras confirmación explícita.

## Flujo conversacional

1. `Registra esta receta para Ensaladilla de gamba`
2. Pegar una o varias líneas del proceso.
3. Escribir `FIN`.
4. Revisar fases, tiempos, tipos y recursos detectados.
5. Escribir `confirma la ficha de producción` o cancelar.

La ficha se guarda en `DATOS/db/fichas_produccion_reales.json`, con copia de seguridad y escritura atómica heredadas de 5.5.6E.3.1.

## Límites de esta entrega

- Entrada de texto pegado, TXT o Markdown.
- No interpreta todavía PDF, DOCX ni imágenes.
- No inventa tiempos ausentes: los deja como pendientes y exige revisión.
