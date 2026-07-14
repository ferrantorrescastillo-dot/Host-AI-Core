# Host AI 4.4.15 - Instalación automática local

## Objetivo

Preparar un instalador local seguro para Host AI que cree las carpetas mínimas, la configuración central y un informe de instalación sin borrar datos existentes.

## Archivos

- `SERVICIOS/instalador_host_ai_4415.py`
- `APP/instalar_host_ai_4415.py`
- `TESTS/test_4415_instalador_host_ai.py`

## Qué crea/verifica

- APP
- CORE
- DATOS
- DATOS/db
- DATOS/configuracion
- DOCS
- Documentos
- LOGS
- MODELOS
- MOTORES
- PIPELINES
- Restaurantes
- SERVICIOS
- TESTS
- Version

## Prueba

```powershell
python TESTS/test_4415_instalador_host_ai.py
```

## Uso manual

```powershell
python APP/instalar_host_ai_4415.py
```

El instalador no elimina archivos ni sustituye lógica existente.
