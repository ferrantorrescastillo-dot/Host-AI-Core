# HOST AI 3.0.4.4 - Predicción Inteligente de Precios

## Añadido
- Modelo `PrediccionPrecioArticulo` e `InformePrediccionPrecios`.
- Servicio `PrediccionInteligentePrecios`.
- Pipeline `prediccion_inteligente_precios`.
- Integración con `HostAICore`, `RegistroPipelines` y `OrquestadorHostAI`.
- Predicción basada en:
  - histórico inteligente de precios,
  - media móvil,
  - tendencia,
  - variación porcentual,
  - predicción siguiente precio,
  - nivel de confianza.
- Exportación JSON de predicciones.

## Comando de prueba
```bash
python TESTS\test_prediccion_inteligente_precios.py
```
