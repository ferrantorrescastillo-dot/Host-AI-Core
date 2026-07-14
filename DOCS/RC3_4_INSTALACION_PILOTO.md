# RC3.4 — Instalación y Arranque para Piloto

## Objetivo

Añadir una verificación mínima para confirmar que una instalación local de Host AI tiene la estructura correcta antes de probarla en restaurante.

## Archivos añadidos

```text
SERVICIOS/verificador_instalacion_piloto.py
TESTS/test_rc3_4_instalacion_piloto.py
DOCS/RC3_4_INSTALACION_PILOTO.md
```

## Qué comprueba

Carpetas mínimas:

```text
APP
CORE
MODELOS
SERVICIOS
PIPELINES
TESTS
DOCS
DATOS
```

Archivos mínimos:

```text
CORE/host_ai_core.py
CORE/orquestador.py
CORE/registro_pipelines.py
TESTS/test_host_ai_3_0_stable.py
```

## Comandos de prueba

```powershell
python TESTS\test_rc3_4_instalacion_piloto.py
python TESTS\test_host_ai_3_0_stable.py
```

## Criterio de aceptación

Debe aparecer:

```text
TEST OK - Host AI RC3.4 Instalación y Arranque para Piloto
```
