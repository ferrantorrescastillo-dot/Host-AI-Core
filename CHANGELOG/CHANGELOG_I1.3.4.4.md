# CHANGELOG — I1.3.4.4 Auditoría e Integridad Postimportación

## Añadido
- Auditor de solo lectura para `DATOS/db/menus.json`.
- Verificación estructural de menús, secciones, platos y componentes.
- Validación de `plato_id` y `componente_id`.
- Detección de componentes huérfanos y relaciones duplicadas.
- Contraste de recetas y artículos con sus catálogos oficiales.
- Recalculo de food cost y beneficio.
- Detección de resúmenes desactualizados y duplicados.
- Estados `CERTIFICADA`, `CERTIFICADA_CON_AVISOS` y `NO_CERTIFICADA`.
- Informes JSON y TXT en `DATOS/auditorias/i1344/`.
- Opción 31 en Excel / Importaciones.
- Diagnóstico aislado sin modificar datos reales.

## Seguridad
- La auditoría nunca modifica menús, recetas ni artículos.
- Solo escribe informes fuera de los catálogos operativos.
- Los errores referenciales impiden certificar, pero no alteran la importación realizada.
