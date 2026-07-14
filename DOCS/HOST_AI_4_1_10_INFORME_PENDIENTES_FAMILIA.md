# Host AI 4.1.10 — Informe de Artículos Pendientes de Familia

## Objetivo

Listar los artículos que siguen sin familia después del clasificador 4.1.9.

## No modifica datos

Este módulo solo genera un informe.

## Comando de prueba

```powershell
python TESTS\test_4110_informe_pendientes_familia.py
```

## Generar informe real

```powershell
python APP\informe_pendientes_familia_4110.py
```

## Archivo generado

```text
DATOS/db/pendientes_familia_4_1_10.txt
```

## Siguiente paso

Con ese listado decidimos:

- nuevas reglas automáticas,
- edición manual de familias,
- o creación de nuevas familias.
