# RC1.1.1 — Auditoría CORE

## Carpeta revisada

`CORE/`

Archivos principales:

- `host_ai_core.py`
- `orquestador.py`
- `registro_pipelines.py`
- `director_host_ai.py`

## Estado

Funcional, pero demasiado centralizado.

El Core carga el sistema y permite registrar y ejecutar pipelines. La arquitectura base funciona, pero el archivo principal conoce demasiados servicios, motores y pipelines.

## Lo que está bien

- `RegistroPipelines` es simple y claro.
- `DirectorHostAI` funciona como capa fina de ejecución.
- `HostAICore` centraliza el arranque del sistema.
- `OrquestadorHostAI` permite conectar intenciones con pipelines.
- Existe una estructura estándar basada en `SolicitudPipeline` y `ResultadoPipeline`.

## Riesgos

- `host_ai_core.py` tiene demasiados imports y demasiada responsabilidad.
- `orquestador.py` puede crecer demasiado con cada nueva intención.
- Cada módulo nuevo puede obligar a tocar Core y Orquestador.
- A largo plazo esto puede dificultar mantenimiento y pruebas.

## Recomendaciones RC1

1. No cambiar funcionalidad todavía.
2. Documentar cómo se registra un pipeline.
3. Separar progresivamente el registro de pipelines por bloques.
4. Evitar que `HostAICore` conozca detalles internos de cada servicio.
5. Mantener `test_host_ai_3_0_stable.py` como test obligatorio tras cada cambio.

## Prioridad

Alta, pero no urgente para piloto inicial si los tests siguen pasando.
