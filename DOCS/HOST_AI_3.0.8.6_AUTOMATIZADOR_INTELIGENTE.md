# HOST AI 3.0.8.6 - Automatizador Inteligente

## Objetivo
Prepara acciones operativas desde lenguaje natural con trazabilidad, control de riesgos y confirmación antes de modificar datos.

## Funciones
- Detectar acciones: pedidos, producción, escandallos, artículos e informes.
- Preparar pipeline destino y parámetros.
- Clasificar acciones con impacto operativo.
- Bloquear ejecución sin confirmación cuando corresponde.
- Ejecutar acciones seguras o confirmadas.

## Integración
- Servicio: `SERVICIOS/automatizador_inteligente_308.py`
- Pipeline: `PIPELINES/pipeline_automatizador_inteligente_308.py`
- Modelo: ampliación de `MODELOS/ia_conversacional_308.py`
- Orquestador: intenciones `preparar_automatizacion_308`, `ejecutar_automatizacion_308`, `validar_confirmacion_automatizacion_308`.

## Test
```bash
python TESTS\test_automatizador_inteligente_308.py
```
