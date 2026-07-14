# HOST AI 5.5.6AB — Escalado real y explosión de elaboraciones

## 5.5.6A — Escalador de recetas

Lee `DATOS/db/escandallos_canonicos.json`, calcula el factor entre el rendimiento base y el objetivo, y escala todos los ingredientes sin modificar datos.

Ejemplos:

```text
Calcula la ensaladilla de gamba para 150 personas.
Escala la receta de crema catalana para 80 raciones.
```

## 5.5.6B — Explosión de elaboraciones

Detecta ingredientes que son recetas internas por `receta_id`, `elaboracion_id` o coincidencia exacta de nombre. Construye un árbol recursivo y consolida los ingredientes finales. Incluye detección de ciclos y límite de profundidad.

Ejemplo:

```text
Desglosa toda la producción de patatas bravas para 100 personas incluyendo elaboraciones internas.
```

## Seguridad

- Solo lectura.
- No crea órdenes de producción.
- No descuenta stock.
- No genera compras.
- No modifica recetas ni artículos.
