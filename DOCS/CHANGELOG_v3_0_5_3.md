# Host AI 3.0.5.3 - Control Inteligente de Entradas y Salidas

## Añadido
- Modelo de líneas de control de movimientos de stock.
- Servicio `ControlInteligenteMovimientosStock`.
- Pipeline `control_inteligente_movimientos_stock`.
- Integración con HostAI Core, Registro de Pipelines y Orquestador.
- Test `TESTS/test_control_inteligente_movimientos_stock.py`.

## Funcionalidad
Analiza entradas, salidas, ajustes, mermas, pérdidas, descuadres y balance por artículo.

## Prueba
```bash
python TESTS\test_control_inteligente_movimientos_stock.py
```
