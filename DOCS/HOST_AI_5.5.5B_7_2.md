# HOST AI 5.5.5B.7.2 — Conector del asistente al modelo canónico

## Objetivo

Conectar las consultas conversacionales de recetas, menús y escandallos con la base canónica creada por la importación 5.5.5B.7.1.

## Prioridad de lectura

1. `DATOS/db/escandallos_canonicos.json`
2. `DATOS/db/escandallos.json` como compatibilidad si la base canónica todavía no contiene registros.

## Seguridad

- Solo lectura.
- No modifica recetas ni artículos.
- No crea ni actualiza archivos durante una consulta.
- No inventa resultados cuando no hay datos.

## Consultas compatibles

- `¿Qué recetas tienes registradas?`
- `¿Qué escandallos tienes disponibles?`
- `Busca una receta que contenga patata.`
- `¿En qué recetas uso patata Monalisa?`
