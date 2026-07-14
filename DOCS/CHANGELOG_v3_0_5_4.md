# Host AI 3.0.5.4 - Reconciliador Inteligente de Stock

## Añadido
- Modelo de diferencias de reconciliación de stock.
- Servicio `ReconciliadorInteligenteStock`.
- Pipeline `reconciliador_inteligente_stock`.
- Integración con HostAI Core, Registro de Pipelines y Orquestador.
- Test `TESTS/test_reconciliador_inteligente_stock.py`.
- Test combinado `TESTS/test_gestion_inteligente_stock_3051_3052_3053_3054.py`.

## Funcionalidad
Compara stock teórico, inventario físico, movimientos, compras y producción para detectar diferencias y proponer acciones.

## Pruebas
```bash
python TESTS\test_reconciliador_inteligente_stock.py
python TESTS\test_gestion_inteligente_stock_3051_3052_3053_3054.py
```
