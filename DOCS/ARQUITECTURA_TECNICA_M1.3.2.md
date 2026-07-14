# M1.3.2 — Arquitectura técnica

`ResolucionIngredientesM132` recibe un `BorradorRecetaM131`, crea una cola únicamente con ingredientes no vinculados y conserva el índice original de cada línea.

Para cada elemento:
1. Crea un checkpoint con el borrador y el índice.
2. Registra un conflicto `ARTICULO / ENTIDAD_NO_EXISTE`.
3. Abre una sesión en el MUR.
4. Delega `VINCULAR` o `CREAR` en M1.2.
5. Aplica el artículo resultante a la línea original.
6. Recalcula el borrador.
7. Cierra el conflicto solo si el artículo ya está vinculado.

La cola puede quedar parcialmente resuelta. Los elementos sin decisión conservan checkpoint, sesión y conflicto para una continuación posterior.
