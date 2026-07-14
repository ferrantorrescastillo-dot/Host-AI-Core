# Host AI 4.5.5 - Panel de estado

## Objetivo

Crear un panel rápido para saber si el proyecto está sano antes de seguir desarrollando o instalarlo en un restaurante.

## Qué revisa

- Carpetas principales: APP, SERVICIOS, TESTS, DATOS, DOCS y LOGS.
- Número de apps, servicios, tests y documentos.
- Estado de la base de datos definitiva.
- Configuración central si existe.
- Restaurante activo o restaurantes registrados.

## Uso

```powershell
python APP/panel_estado_455.py
```

## Test

```powershell
python TESTS/test_455_panel_estado.py
```
