# HOST AI 3.0.4.3 - Detector Inteligente de Anomalías de Compras

## Añadido
- Modelo `AnomaliaCompra` e `InformeAnomaliasCompras`.
- Servicio `DetectorAnomaliasCompras`.
- Pipeline `detector_anomalias_compras`.
- Integración con `HostAICore`, `RegistroPipelines` y `OrquestadorHostAI`.
- Detección de:
  - subidas anormales de precio,
  - bajadas sospechosas,
  - facturas duplicadas,
  - artículos desconocidos o con baja confianza,
  - cantidades fuera de rango,
  - errores OCR detectables,
  - proveedores con comportamiento extraño.
- Clasificación por gravedad: `informativa`, `aviso`, `critica`.
- Exportación JSON de informe.

## Comando de prueba
```bash
python TESTS\test_detector_anomalias_compras.py
```
