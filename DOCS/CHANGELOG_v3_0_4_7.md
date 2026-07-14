# HOST AI 3.0.4.7 - Motor Inteligente de Pedidos

## Añadido
- Modelo `DecisionPedidoInteligente`.
- Servicio `MotorInteligentePedidos`.
- Pipeline `motor_inteligente_pedidos`.
- Integración con Core, Registro de Pipelines y Orquestador.
- Test individual `test_motor_inteligente_pedidos.py`.

## Funcionalidad
El motor transforma roturas de stock, predicciones de precio, comparador de proveedores y anomalías en decisiones operativas:
- comprar,
- esperar,
- cambiar proveedor,
- no comprar todavía.

## Comando
```bash
python TESTS\test_motor_inteligente_pedidos.py
```
