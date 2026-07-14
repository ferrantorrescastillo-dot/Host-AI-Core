# HOST AI 3.0.4.4 - Predicción Inteligente de Precios

Este módulo calcula predicciones de precio a partir del histórico real guardado por Host AI.

## Pipeline

`prediccion_inteligente_precios`

## Acciones

- `predecir`
- `predecir_articulo`
- `exportar`

## Intenciones del Orquestador

```python
SolicitudHostAI("predecir_precios_compras", {"ventana": 3})
SolicitudHostAI("predecir_precio_articulo", {"articulo_id": "ART-CARRILLERA", "ventana": 3})
SolicitudHostAI("exportar_prediccion_precios", {"informe": informe, "nombre": "prediccion.json"})
```

## Prueba Windows

```bash
python TESTS\test_prediccion_inteligente_precios.py
```
