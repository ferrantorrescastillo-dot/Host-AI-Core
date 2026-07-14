# HOST AI 5.1 — Núcleo IA

## Objetivo

El bloque 5.1 inicia Host AI 5.0 creando el primer núcleo cognitivo central.

No sustituye a los módulos existentes. Su función es entender una solicitud natural,
detectar qué áreas deben intervenir y preparar un plan seguro usando los motores ya
construidos en Host AI 4.x.

## Archivos incluidos

- `APP/nucleo_ia_host_ai_51.py`
- `SERVICIOS/nucleo_ia_host_ai_51.py`
- `TESTS/test_51_nucleo_ia_host_ai.py`
- `DOCS/HOST_AI_5_1_NUCLEO_IA.md`

## Funciones principales

- `detectar_areas_solicitud`
- `extraer_datos_basicos_solicitud`
- `construir_contexto_operativo`
- `generar_plan_nucleo`
- `evaluar_con_motores_existentes`
- `procesar_solicitud_nucleo_ia`

## Principio de seguridad

El núcleo 5.1 trabaja en modo propuesta segura: analiza, decide y propone, pero no
ejecuta cambios reales sin confirmación.

## Prueba

```powershell
python -m TESTS.test_51_nucleo_ia_host_ai
```

## Uso manual

```powershell
python APP/nucleo_ia_host_ai_51.py
```
