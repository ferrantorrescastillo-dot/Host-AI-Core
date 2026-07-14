# Prompt Operativo para Copilot

Objetivo: Compras
Dominio: compras

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
- APP/compras_evento_474.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- MODELOS/analisis_compras.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- MODELOS/anomalias_compras.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- MODELOS/cierre_inteligencia_compras.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- MODELOS/compras.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- MODELOS/recomendaciones_compras.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- MOTORES/motor_compras.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- PIPELINES/pipeline_analizador_inteligente_compras.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- PIPELINES/pipeline_cierre_inteligencia_compras.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- PIPELINES/pipeline_compras.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- PIPELINES/pipeline_detector_anomalias_compras.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- PIPELINES/pipeline_motor_recomendaciones_compras.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- SERVICIOS/analizador_inteligente_compras.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- SERVICIOS/cierre_inteligencia_compras.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- SERVICIOS/compras_evento_474.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- SERVICIOS/detector_anomalias_compras.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- SERVICIOS/integrador_compras_escandallos_555a.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- SERVICIOS/motor_recomendaciones_compras.py (p=62, motivo=match_keyword:compra,match_keyword:compras)
- TESTS/test_474_compras_evento.py (p=58, motivo=match_keyword:compra,match_keyword:compras)
- TESTS/test_508_afinador_compras_rentabilidad.py (p=58, motivo=match_keyword:compra,match_keyword:compras)

## Tests relacionados
- TESTS/test_4112_clasificador_familias_proveedor.py (match_keyword:proveedor)
- TESTS/test_421_extractor_proveedores.py (match_keyword:proveedor)
- TESTS/test_422_editor_proveedores.py (match_keyword:proveedor)
- TESTS/test_423_informe_proveedores.py (match_keyword:proveedor)
- TESTS/test_435_pedido_sugerido_stock_bajo.py (match_keyword:pedido)
- TESTS/test_436_confirmador_pedido_sugerido.py (match_keyword:pedido)
- TESTS/test_438_entrada_stock_desde_pedido.py (match_keyword:pedido)
- TESTS/test_474_compras_evento.py (match_stem:compras)
- TESTS/test_486_comparador_economico_proveedores.py (match_keyword:proveedor)
- TESTS/test_508_afinador_compras_rentabilidad.py (match_stem:test_508_afinador_compras_rentabilidad)
- TESTS/test_554_conector_proveedores_real.py (match_keyword:proveedor)
- TESTS/test_604_c1_gestion_compras.py (match_stem:compras)
- TESTS/test_604_c2_pedido_operativo.py (match_keyword:pedido)
- TESTS/test_604_ux1_flujos_consola.py (match_stem:consola)
- TESTS/test_analizador_inteligente_compras.py (match_stem:test_analizador_inteligente_compras)
- TESTS/test_aprendizaje_relacion_proveedor.py (match_stem:aprendizaje_relacion_proveedor)
- TESTS/test_cierre_inteligencia_compras.py (match_stem:compras)
- TESTS/test_comparador_inteligente_proveedores.py (match_stem:comparador_inteligente_proveedores)
- TESTS/test_comparador_proveedores_precios.py (match_stem:comparador_proveedores_precios)
- TESTS/test_detector_anomalias_compras.py (match_stem:detector_anomalias_compras)

## Entrega esperada
- Implementacion acotada al objetivo.
- Tests relevantes en verde.
- Resumen tecnico de cambios con riesgos.
