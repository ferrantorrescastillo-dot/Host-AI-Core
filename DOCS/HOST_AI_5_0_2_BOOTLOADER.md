# HOST AI 5.0.2 - Bootloader

## Objetivo

Crear un punto de entrada unico para Host AI:

```powershell
python main.py
```

El bootloader evita tener que ejecutar archivos sueltos como:

```powershell
python APP/algo.py
```

Ese formato puede provocar errores en Windows como:

```text
ModuleNotFoundError: No module named 'SERVICIOS'
```

## Archivos incluidos

- `main.py`
- `APP/bootloader_host_ai_502.py`
- `SERVICIOS/bootloader_host_ai_502.py`
- `TESTS/test_502_bootloader_host_ai.py`
- `DOCS/HOST_AI_5_0_2_BOOTLOADER.md`

## Como probar

Desde la raiz del proyecto:

```powershell
python -m TESTS.test_502_bootloader_host_ai
```

## Como usar

```powershell
python main.py
```

A partir de este sprint, Host AI debe tender a ejecutarse siempre desde `main.py`.

## Nota importante

Este parche no sustituye los motores existentes. Solo crea una capa segura para lanzar el sistema desde un unico punto.
