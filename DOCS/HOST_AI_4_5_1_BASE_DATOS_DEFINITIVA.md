# HOST AI 4.5.1 - Base de Datos Definitiva

## Objetivo

Preparar una base SQLite central (`DATOS/db/host_ai.db`) para que Host AI deje de depender únicamente de archivos JSON sueltos.

Este sprint no borra ni sustituye los JSON actuales. Solo crea una capa estable para los siguientes módulos.

## Incluye

- Creación/verificación de tablas principales.
- Tabla de configuración.
- Tabla de logs.
- Tablas de artículos, proveedores, stock, pedidos, recepciones e histórico de precios.
- Migración básica no destructiva desde `articulos.json` y `proveedores.json`.

## Uso

```powershell
python APP/base_datos_definitiva_451.py
```

## Test

```powershell
python TESTS/test_451_base_datos_definitiva.py
```
