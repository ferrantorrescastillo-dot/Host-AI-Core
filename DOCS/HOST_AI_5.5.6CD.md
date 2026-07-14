# HOST AI 5.5.6CD

## 5.5.6C — Cruce con stock real

Explota la receta hasta ingredientes finales, consulta `stock_inicial.json` y el último `stock_despues` disponible, convierte kg/g y l/ml, y devuelve necesario, disponible, faltante y restante. Solo lectura.

## 5.5.6D — Plan preliminar de producción

Genera fases operativas: preparar, elaborar/cocinar, enfriar o reposar cuando corresponda, porcionar, envasar, etiquetar, guardar y control final. Informa de tiempos activos/pasivos y bloquea el plan si hay faltantes. No crea órdenes reales.

## Pruebas

```powershell
python TESTS/test_556cd_stock_plan.py
python APP/probar_cruce_stock_plan_556cd.py "Ensaladilla de gamba" 150
python APP/probar_cruce_stock_plan_556cd.py "Ensaladilla de gamba" 150 --plan
```
