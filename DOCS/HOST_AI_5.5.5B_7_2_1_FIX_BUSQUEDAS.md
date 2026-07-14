# HOST AI 5.5.5B.7.2.1 — Corrección de búsquedas canónicas

Corrige dos rutas que todavía consultaban `DATOS/db/escandallos.json`:

- búsqueda de recetas por ingrediente;
- búsqueda de recetas por nombre o texto parcial.

A partir de este parche, ambas consultas usan primero `DATOS/db/escandallos_canonicos.json` mediante el lector canónico 5.5.5B.7.2.

También corrige la extracción de términos en frases como:

- `¿En qué recetas uso patata Monalisa?`
- `Busca una receta que contenga ensaladilla.`
- `Muéstrame el escandallo de ensaladilla de gamba.`

El parche es de solo lectura y no modifica recetas.
