# HOST AI 5.5.5B — Parte 1

## Objetivo

Crear la primera capa del importador universal de escandallos Excel sobre el modelo canónico 5.5.5A.

## Incluye

- Apertura segura de archivos `.xlsx` y `.xlsm`.
- Lectura con `openpyxl` en modo `read_only`.
- Detección automática de la fila de cabecera.
- Detección de hojas candidatas a escandallos.
- Vista previa de filas sin modificar el Excel.
- Propuesta de mapeo hacia campos canónicos.
- Perfil de mapeo reutilizable y guardado atómico.

## Campos mínimos

- RECETA
- INGREDIENTE
- CANTIDAD
- UNIDAD

## Seguridad

Esta parte no importa, no actualiza y no elimina escandallos. No escribe en la base de datos de Host AI.

## Prueba

```powershell
python TESTS/test_555b_parte1.py
```

## Vista previa sobre un Excel real

```powershell
python APP/vista_previa_importador_escandallos_555b.py "C:\ruta\escandallos.xlsx"
```
