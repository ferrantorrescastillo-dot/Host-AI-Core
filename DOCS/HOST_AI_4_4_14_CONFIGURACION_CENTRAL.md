# Host AI 4.4.14 - Configuración centralizada

## Objetivo

Crear un único punto de configuración para Host AI, evitando que cada módulo tenga rutas, idioma, OCR, IA, IVA o restaurante definidos por separado.

## Archivos

- `SERVICIOS/configuracion_central_4414.py`
- `APP/configuracion_host_ai_4414.py`
- `TESTS/test_4414_configuracion_central.py`

## Archivo generado

La configuración se guarda en:

```text
DATOS/configuracion/host_ai_config.json
```

## Campos principales

- restaurante
- iva_default
- moneda
- idioma
- ruta_datos
- ruta_documentos
- ruta_logs
- ocr_activo
- ia_activa
- proveedor_default
- modo_entorno

## Prueba

```powershell
python TESTS/test_4414_configuracion_central.py
```

## Uso manual

```powershell
python APP/configuracion_host_ai_4414.py
```
