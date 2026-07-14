# Host AI 3.0.2.8 - Asistente Completo de Importación Excel

## Objetivo
Unificar todo el flujo de importación Excel en un asistente único.

## Añade
- `MODELOS/asistente_importacion_excel.py`
- `SERVICIOS/asistente_importacion_excel.py`
- `PIPELINES/pipeline_asistente_importacion_excel.py`
- `TESTS/test_asistente_importacion_excel.py`

## Nuevas intenciones
- `preparar_importacion_excel`
- `ejecutar_importacion_excel`
- `listar_sesiones_importacion_excel`

## Flujo
1. Analizar Excel.
2. Detectar tipo.
3. Mapear columnas.
4. Detectar conflictos.
5. Vista previa.
6. Ejecutar importador correcto.

## Prueba
```powershell
python TESTS\test_asistente_importacion_excel.py
```
