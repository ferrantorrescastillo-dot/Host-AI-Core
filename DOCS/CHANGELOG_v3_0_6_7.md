# Host AI 3.0.6.7 - Optimizador Inteligente de Producción

## Añadido
- Modelo `OportunidadOptimizacionProduccion`.
- Modelo `InformeOptimizacionProduccion`.
- Servicio `OptimizadorInteligenteProduccion`.
- Pipeline `optimizador_inteligente_produccion`.
- Integración en HostAI Core, Registro de Pipelines y Orquestador.
- Test individual `TESTS/test_optimizador_inteligente_produccion.py`.

## Funcionalidades
- Detecta oportunidades por tiempos pasivos largos.
- Agrupa tareas por recurso.
- Detecta huecos operativos en recursos.
- Equilibra carga de cocineros.
- Incorpora control y replanificación previa.
- Genera plan optimizado e informe exportable.

## Comando de prueba
```bash
python TESTS\test_optimizador_inteligente_produccion.py
```
