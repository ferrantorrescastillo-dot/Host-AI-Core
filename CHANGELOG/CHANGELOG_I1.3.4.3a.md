# CHANGELOG I1.3.4.3a — Corrección del modo R

## Correcciones
- Añadido el import correcto de `Path` en `APP/consola.py`.
- Centralizada la carga y validación de sesiones revisadas en `ImportadorDefinitivoMenusI1343.cargar_sesion_revisada()`.
- Soporte para rutas absolutas y relativas, incluyendo rutas con espacios.
- Validación previa de existencia, tipo de archivo y extensión JSON.
- Mensajes explícitos para JSON corrupto o estructura de sesión inválida.
- Rechazo de sesiones con pendientes, bloqueantes o planes no listos.
- La validación se ejecuta antes de iniciar cualquier transacción o escritura.

## Seguridad
- No modifica datos reales durante la validación.
- No cambia la lógica de commit, rollback o idempotencia ya certificada.
- Mantiene bloqueada la importación si la sesión no está en `LISTA_PARA_TRANSACCION`.
