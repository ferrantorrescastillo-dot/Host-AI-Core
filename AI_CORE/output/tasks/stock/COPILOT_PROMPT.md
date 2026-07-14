# Prompt Operativo para Copilot

Objetivo: Stock
Dominio: stock

## Restricciones
- No tocar DATOS, DB ni Documentos/AI.docx.
- No romper AI_CORE v1/v2.1.
- Cambios minimos y verificables.

## Documentacion prioritaria
- AGENTS.md (p=2)
- MASTER_PLAN.md (p=3)
- CODEX-01.md (p=4)
- CODEX-02.md (p=5)
- ROC/ROC-01A_NUCLEO.md (p=110)
- ROC/ROC-01B_NUCLEO.md (p=110)
- ROC/ROC-02A_OPERACION.md (p=110)
- ROC/ROC-02B_OPERACION.md (p=110)

## Archivos de codigo foco
- APP/historial_movimientos_stock_4310.py (p=62, motivo=match_keyword:stock,match_keyword:movimiento)
- APP/movimiento_stock_437.py (p=62, motivo=match_keyword:stock,match_keyword:movimiento)
- MODELOS/control_movimientos_stock_305.py (p=62, motivo=match_keyword:stock,match_keyword:movimiento)
- PIPELINES/pipeline_control_inteligente_movimientos_stock.py (p=62, motivo=match_keyword:stock,match_keyword:movimiento)
- SERVICIOS/control_inteligente_movimientos_stock.py (p=62, motivo=match_keyword:stock,match_keyword:movimiento)
- SERVICIOS/historial_movimientos_stock_4310.py (p=62, motivo=match_keyword:stock,match_keyword:movimiento)
- SERVICIOS/motor_movimientos_stock_437.py (p=62, motivo=match_keyword:stock,match_keyword:movimiento)
- TESTS/test_4310_historial_movimientos_stock.py (p=58, motivo=match_keyword:stock,match_keyword:movimiento)
- TESTS/test_437_motor_movimientos_stock.py (p=58, motivo=match_keyword:stock,match_keyword:movimiento)
- TESTS/test_control_inteligente_movimientos_stock.py (p=58, motivo=match_keyword:stock,match_keyword:movimiento)
- APP/alertas_stock_bajo_434.py (p=47, motivo=match_keyword:stock)
- APP/aplicar_ajustes_inventario_43114.py (p=47, motivo=match_keyword:inventario)
- APP/cierre_modulo_stock_4312.py (p=47, motivo=match_keyword:stock)
- APP/comparar_inventario_43113.py (p=47, motivo=match_keyword:inventario)
- APP/conector_stock_real_553.py (p=47, motivo=match_keyword:stock)
- APP/entrada_stock_desde_pedido_438.py (p=47, motivo=match_keyword:stock)
- APP/generar_plantilla_inventario_43111.py (p=47, motivo=match_keyword:inventario)
- APP/generar_plantilla_stock_431.py (p=47, motivo=match_keyword:stock)
- APP/gestionar_inventario_inicial_556cd2.py (p=47, motivo=match_keyword:inventario)
- APP/importar_inventario_43112.py (p=47, motivo=match_keyword:inventario)

## Tests relacionados
- TESTS/test_4310_historial_movimientos_stock.py (match_stem:test_4310_historial_movimientos_stock)
- TESTS/test_43111_plantilla_inventario.py (match_keyword:inventario)
- TESTS/test_43112_importador_inventario.py (match_keyword:inventario)
- TESTS/test_43113_comparador_inventario.py (match_keyword:inventario)
- TESTS/test_43114_aplicador_ajustes_inventario.py (match_keyword:inventario)
- TESTS/test_43115_informe_final_inventario.py (match_keyword:inventario)
- TESTS/test_4312_cierre_modulo_stock.py (match_stem:stock)
- TESTS/test_431_plantilla_stock_inicial.py (match_stem:stock)
- TESTS/test_432_importador_stock_inicial.py (match_stem:stock)
- TESTS/test_433_informe_stock_inicial.py (match_stem:stock)
- TESTS/test_434_alertas_stock_bajo.py (match_stem:stock)
- TESTS/test_435_pedido_sugerido_stock_bajo.py (match_stem:stock)
- TESTS/test_437_motor_movimientos_stock.py (match_stem:test_437_motor_movimientos_stock)
- TESTS/test_438_entrada_stock_desde_pedido.py (match_stem:stock)
- TESTS/test_439_salidas_stock.py (match_stem:stock)
- TESTS/test_553_conector_stock_real.py (match_stem:stock)
- TESTS/test_556cd1_enlace_canonico_stock.py (match_stem:stock)
- TESTS/test_556cd2_inventario_inicial_seguro.py (match_keyword:inventario)
- TESTS/test_556cd_stock_plan.py (match_stem:stock)
- TESTS/test_actualizador_inteligente_stock_factura.py (match_stem:stock)

## Entrega esperada
- Implementacion acotada al objetivo.
- Tests relevantes en verde.
- Resumen tecnico de cambios con riesgos.
