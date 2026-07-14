# I1.3.4.1.3 — Bandeja de revisión y limpieza masiva

La bandeja consume el plan de I1.3.4.1.2 y crea una sesión separada en `DATOS/mur/revisiones_i13413/`.

## Incidencias incluidas
1. Todas las acciones bloqueadas.
2. Complementos o artículos directos cuyo nombre parece una elaboración culinaria.
3. Elementos de baja confianza que requieren decisión humana.

## Acciones
- `ELIMINAR`: retira el elemento y sus relaciones del plan, nunca del Excel.
- `CLASIFICAR`: cambia el destino de importación de uno o varios elementos.
- `RENOMBRAR`: cambia el nombre únicamente en el plan revisado.
- `VINCULAR`: convierte un bloqueo en vínculo a receta o artículo.
- `MANTENER`: cierra avisos; un bloqueo permanece abierto por seguridad.

Cada cambio recalcula el plan. Solo se muestra `LISTA_PARA_TRANSACCION` cuando no quedan bloqueos.
