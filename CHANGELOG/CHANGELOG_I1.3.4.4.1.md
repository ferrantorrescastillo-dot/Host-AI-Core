# I1.3.4.4.1 — Bandeja de corrección postimportación

## Objetivo
Convertir las incidencias detectadas por I1.3.4.4 en una bandeja operativa para corregir el catálogo real de menús sin editar JSON manualmente.

## Funciones
- Lista numerada de errores y avisos.
- Eliminación individual o múltiple de relaciones, artículos directos, platos, secciones o menús según incidencia.
- Renombrado de menú, plato o componente.
- Vinculación con recetas y artículos existentes.
- Cambio y creación controlada de secciones.
- Recalculo de food cost y beneficio.
- Vista previa aislada antes de guardar.
- Persistencia de sesión y trazabilidad de acciones.
- Backup, escritura atómica, commit y rollback mediante I1.3.4.2.
- Reauditoría automática después del commit.

## Seguridad
- Nada se escribe mientras se revisa.
- Para aplicar cambios reales hay que elegir `G` y escribir exactamente `GUARDAR`.
- Las recetas y artículos nuevos no se inventan: se crean en sus módulos oficiales y después se vinculan desde la bandeja.
- Toda escritura queda protegida con backup y rollback.

## Nueva opción
`32. I1.3.4.4.1 Bandeja de corrección postimportación`

## Certificación
- Tests específicos + auditoría + escritura segura + importación: 31/31.
- Diagnóstico aislado: CERTIFICADA, 0 errores, 0 avisos.
- Datos reales modificados durante las pruebas: 0.
