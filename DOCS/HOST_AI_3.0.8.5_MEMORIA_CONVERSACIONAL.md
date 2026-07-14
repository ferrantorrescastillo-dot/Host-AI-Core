# HOST AI 3.0.8.5 - Memoria Conversacional

## Objetivo
Añade memoria conversacional persistente para mantener contexto operativo entre consultas de IA conversacional.

## Funciones
- Recordar claves de contexto.
- Consultar memoria por clave, tipo o tags.
- Resolver referencias como "ese producto", "lo mismo" o "el anterior".
- Aprender entidades desde turnos conversacionales.
- Exportar memoria a `DATOS/ia_conversacional/memoria_conversacional_3085.json`.

## Integración
- Servicio: `SERVICIOS/memoria_conversacional_308.py`
- Pipeline: `PIPELINES/pipeline_memoria_conversacional_308.py`
- Modelo: ampliación de `MODELOS/ia_conversacional_308.py`
- Orquestador: intenciones `recordar_memoria_conversacional_308`, `consultar_memoria_conversacional_308`, `resolver_referencias_memoria_308`.

## Test
```bash
python TESTS\test_memoria_conversacional_308.py
```
