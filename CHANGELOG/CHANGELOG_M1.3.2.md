# CHANGELOG M1.3.2

## Añadido
- Cola estable de conflictos de ingredientes no resueltos.
- Un checkpoint MUR por ingrediente.
- Delegación real en `ResolutorArticulosM12`.
- Reanudación del borrador después de cada resolución.
- Soporte para varios conflictos anidados en una misma receta.
- Política configurable para artículos sin precio.
- Diagnóstico aislado y reproducible.

## Reglas preservadas
- `M.P` = Materia Prima.
- `A.P` = Aperitivo y no se propone automáticamente como ingrediente base.
- Falta de unidad = bloqueo.
- Falta de precio = artículo `PENDIENTE` cuando la política lo permite.
- Sin decisión explícita = conflicto abierto y borrador bloqueado.

## No incluido
- Creación definitiva de la receta.
- Resolución interactiva de producción.
- Proveedores, familias o unidades como subconflictos propios.
