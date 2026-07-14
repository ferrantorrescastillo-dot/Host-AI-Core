# HOST AI 3.0.4.3 - Detector Inteligente de Anomalías

Este módulo analiza compras desde el histórico de precios, histórico de stock y auditoría del Importador Universal.

## Pipeline

`detector_anomalias_compras`

## Acciones

- `detectar`
- `exportar`

## Intenciones del Orquestador

```python
SolicitudHostAI("detectar_anomalias_compras", {})
SolicitudHostAI("exportar_anomalias_compras", {"informe": informe, "nombre": "anomalias.json"})
```

## Prueba Windows

```bash
python TESTS\test_detector_anomalias_compras.py
```
