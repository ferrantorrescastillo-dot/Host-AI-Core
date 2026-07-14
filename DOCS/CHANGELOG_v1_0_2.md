# Host AI 2.0 v1.0.2 - Pipeline de Compras Inicial

## Objetivo

Añadir el primer pipeline operativo fuera de eventos.

## Qué añade

- MODELOS/compras.py
- MOTORES/motor_compras.py
- PIPELINES/pipeline_compras.py
- Atajos de orquestador para compras
- TESTS/test_pipeline_compras.py

## Nuevas intenciones

- registrar_necesidad_compra
- listar_necesidades_compra
- diagnosticar_compras
- generar_pedidos_sugeridos

## Cómo probar

```powershell
cd "C:\Proyecto Host IA 2.0\Host IA 2.0"
python TESTS\test_pipeline_compras.py
```

Resultado esperado:

```text
TEST OK - Host AI v1.0.2 Pipeline de Compras Inicial
```
