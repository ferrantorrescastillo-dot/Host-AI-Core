# Host AI 4.5.6 - Usuarios y roles básicos

## Objetivo

Preparar Host AI para funcionar como producto multiusuario sin convertirlo todavía en una aplicación web.

## Roles base

- admin
- gerente
- jefe_cocina
- compras
- cocinero

## Qué incluye

- Tabla `roles`.
- Tabla `usuarios`.
- Crear usuario.
- Listar usuarios.
- Cambiar rol.
- Desactivar usuario.
- Ocultación del hash de contraseña en las respuestas.

## Uso

```powershell
python APP/usuarios_roles_456.py
```

## Test

```powershell
python TESTS/test_456_usuarios_roles.py
```
