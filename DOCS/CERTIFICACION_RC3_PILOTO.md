# Certificación RC3 — Piloto Host AI

## Objetivo

Confirmar que Host AI 3.0 RC3 está preparado para iniciar una primera prueba piloto controlada.

## Archivos añadidos

```text
SERVICIOS/certificador_piloto_host_ai.py
TESTS/test_rc3_5_certificacion_piloto.py
DOCS/CERTIFICACION_RC3_PILOTO.md
VERSION.txt
```

## Estados posibles

```text
APTO PARA PILOTO
APTO CON OBSERVACIONES
NO APTO
```

## Qué comprueba

- Estructura mínima del proyecto.
- Archivos críticos de CORE.
- Tests críticos.
- Servicios RC3.
- Documentación mínima.
- Carpeta de logs.
- Versionado.

## Comandos de validación

```powershell
python TESTS\test_rc3_5_certificacion_piloto.py
python TESTS\test_host_ai_3_0_stable.py
```

## Interpretación

Si el test muestra:

```text
TEST OK - Host AI RC3.5 Certificación para Piloto
```

entonces Host AI puede pasar a preparación de piloto.

Si el estado final es:

```text
APTO CON OBSERVACIONES
```

significa que la base técnica está preparada, pero hay detalles menores pendientes como documentación, logs o versionado.

Si el estado final es:

```text
NO APTO
```

hay que corregir los errores antes de probarlo en restaurante.
