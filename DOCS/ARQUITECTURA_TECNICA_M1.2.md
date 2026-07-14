# Arquitectura técnica M1.2

`ResolutorArticulosM12` implementa `IResolutorMUR` y no modifica el núcleo MUR.

## Responsabilidades
- Preparar candidatos usando `BuscadorInteligenteArticulos415`.
- Vincular artículos existentes.
- Crear artículos a través de `GestorArticulos416`.
- Completar precio, proveedor, familia o unidad.
- Validar unidad crítica, duplicados y política de precio.
- Devolver `ResultadoResolucion` al orquestador.

## Política de calidad
- Sin unidad: BLOQUEADA.
- Con unidad y sin precio: PENDIENTE si la política lo permite.
- Con unidad y precio: COMPLETA.

## Persistencia
Las escrituras reales usan el catálogo indicado al construir el resolutor. El diagnóstico utiliza una copia aislada. Antes de altas o ediciones se genera backup.
