# CHANGELOG — I1.3.2.4

## Añadido
- Motor de aprendizaje culinario auditable.
- Memoria persistente en `DATOS/db/aprendizaje_culinario_i1324.json`.
- Migración automática de `memoria_resoluciones_menu_i1323.json`.
- Historial de altas, ediciones, desactivaciones y aplicaciones automáticas.
- Contador de usos, confianza, origen, estado y marcas temporales.
- Gestión desde consola: listar, editar y desactivar aprendizajes.
- Aplicación automática de decisiones aprendidas en nuevas vistas previas.

## Seguridad
- Solo guarda decisiones con confirmación explícita.
- No crea recetas ni artículos.
- No importa menús.
- Desactivar conserva el historial; no borra de forma destructiva.
