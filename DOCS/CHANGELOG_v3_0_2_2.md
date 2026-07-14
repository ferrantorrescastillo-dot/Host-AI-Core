# Host AI 3.0.2.2 - Detector Inteligente de Documentos Excel

## Objetivo

Detectar automáticamente el tipo de documento/hoja Excel.

## Detecta

- escandallo
- listado_articulos
- inventario
- compras
- produccion
- proveedores
- desconocido

## Añade

- `MODELOS/deteccion_excel.py`
- `SERVICIOS/detector_documentos_excel.py`
- `PIPELINES/pipeline_detector_excel.py`
- `TESTS/test_detector_documentos_excel.py`

## Nuevas intenciones

- `detectar_documento_excel`
- `detectar_documento_desde_analisis_excel`

## Prueba

```powershell
python TESTS\test_detector_documentos_excel.py
```
