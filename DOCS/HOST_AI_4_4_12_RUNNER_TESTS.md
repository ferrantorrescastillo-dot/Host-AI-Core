# Host AI 4.4.12 - Runner inteligente de tests

## Objetivo

Centralizar la ejecución de pruebas para no tener que recordar nombres concretos de archivos en `TESTS`.

## Archivos

- `SERVICIOS/runner_tests_4412.py`
- `APP/test_center_4412.py`
- `TESTS/test_4412_runner_tests.py`

## Uso manual

Desde la raíz del proyecto:

```powershell
python APP/test_center_4412.py
```

Después seleccionar:

```text
1 Catálogo
2 Proveedores
3 Stock
4 Recepción
5 Compras
6 Producción
7 IA
8 Todos
```

## Uso directo por código

```python
from SERVICIOS.runner_tests_4412 import RunnerTests4412
runner = RunnerTests4412(BASE_DIR)
informe = runner.ejecutar_bloque("4")
runner.imprimir_informe(informe)
```

## Integración

El runner no modifica los tests actuales. Los ejecuta como scripts separados usando el Python actual, respetando la arquitectura existente.
